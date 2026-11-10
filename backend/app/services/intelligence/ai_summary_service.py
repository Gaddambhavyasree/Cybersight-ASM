"""AI-powered report summaries and a grounded Q&A "copilot" over scan data.

Privacy model: hostnames/URLs are replaced with ASSET-n placeholders before
anything leaves the process (unless LLM_SEND_HOSTNAMES=true), and IDs are
substituted back server-side afterwards. When no LLM key is configured the
service falls back to a deterministic local summary builder, so report
generation always succeeds.
"""

import json
import logging
import re
from collections import Counter

import httpx
from bson import ObjectId

from app.config import get_settings

logger = logging.getLogger(__name__)

HOST_RE = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")


def _alias_map(texts: list[str]) -> dict[str, str]:
    """Collect candidate hostnames across texts and map them to ASSET-n."""
    mapping: dict[str, str] = {}
    for text in texts:
        for token in re.findall(r"[a-zA-Z0-9._-]+", text or ""):
            token = token.strip(".-").lower()
            if token.count(".") >= 1 and HOST_RE.match(token) and token not in mapping:
                mapping[token] = f"ASSET-{len(mapping) + 1}"
    return mapping


def redact(text: str, mapping: dict[str, str]) -> str:
    out = text or ""
    for host, alias in mapping.items():
        out = re.sub(re.escape(host), alias, out, flags=re.IGNORECASE)
    out = re.sub(r"https?://[^\s\"']+", "[URL-REDACTED]", out) if mapping else out
    return out


def unredact(text: str, mapping: dict[str, str]) -> str:
    out = text or ""
    for host, alias in mapping.items():
        out = re.sub(re.escape(alias), host, out, flags=re.IGNORECASE)
    return out


def llm_configured() -> bool:
    return bool(get_settings().LLM_API_KEY)


async def _chat(system: str, user: str) -> str | None:
    s = get_settings()
    if not llm_configured():
        return None
    payload = {
        "model": s.LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.2,
        "max_tokens": 900,
    }
    try:
        timeout = httpx.Timeout(45.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{s.LLM_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {s.LLM_API_KEY}"},
                json=payload,
            )
        if response.status_code not in (200, 201):
            logger.warning("LLM request failed (%s): %s", response.status_code, response.text[:200])
            return None
        return (response.json().get("choices") or [{}])[0].get("message", {}).get("content")
    except Exception:
        logger.exception("LLM request failed")
        return None


def _percent(x) -> int:
    try:
        return int(round(float(x) * 100))
    except (TypeError, ValueError):
        return 0


async def build_context(db, scan_id: str) -> tuple[dict, dict]:
    """Gathers aggregate context plus alias mapping. Returns (context, alias_map)."""
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        return {}, {}
    project_id = str(scan.get("project_id"))
    assets = await db.assets.find({"project_id": project_id}).to_list(2000)
    vulns = await db.vulnerabilities.find({"scan_id": scan_id}).to_list(2000)
    ports = await db.ports.find({"scan_id": scan_id, "state": "open"}).to_list(2000)
    ssls = await db.ssl_analysis.find({"scan_id": scan_id}).to_list(1000)

    sev = Counter(str(v.get("severity", "low")).lower() for v in vulns)
    top_vulns = sorted(vulns, key=lambda v: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(str(v.get("severity", "low")).lower(), 4),
        -(v.get("epss") or 0),
        -1 if v.get("kev") else 0,
    ))[:15]
    risky_assets = sorted(assets, key=lambda a: -(a.get("risk_score") or 0))[:8]
    high_ports = [p.get("port") for p in ports if p.get("port") in {21, 22, 23, 25, 445, 3306, 3389, 5432, 6379, 9200, 27017}]
    expired = [s.get("hostname") for s in ssls if s.get("expired")]

    texts = [v.get("hostname") or "" for v in vulns] + [a.get("hostname") or "" for a in risky_assets]
    mapping = _alias_map(texts) if not get_settings().LLM_SEND_HOSTNAMES else {}

    context = {
        "project": scan.get("project_name"),
        "target": scan.get("target_domain"),
        "assets_total": len(assets),
        "live_assets": sum(1 for a in assets if a.get("is_live")),
        "open_ports": len(ports),
        "high_risk_ports": high_ports[:15],
        "expired_certificates": [mapping.get(h, h) for h in expired][:5],
        "severity_counts": {k: sev.get(k, 0) for k in ("critical", "high", "medium", "low", "info")},
        "risk_summary": {
            "average": round(sum(a.get("risk_score") or 0 for a in assets) / len(assets)) if assets else 0,
            "top_assets": [{"asset": mapping.get(a.get("hostname"), a.get("hostname")), "score": a.get("risk_score"),
                            "level": a.get("risk_level")} for a in risky_assets],
        },
        "findings": [{
            "finding": (v.get("template_name") or v.get("cve") or "finding")[:80],
            "severity": v.get("severity"),
            "asset": mapping.get(v.get("hostname"), v.get("hostname")),
            "cve": v.get("cve"),
            "kev": bool(v.get("kev")),
            "epss_percent": _percent(v.get("epss")) or None,
        } for v in top_vulns],
    }
    return context, mapping


async def generate_report_summary(db, scan_id: str) -> dict:
    """Returns {"summary": str, "source": "llm"|"local"} for a completed scan."""
    context, mapping = await build_context(db, scan_id)
    local = local_summary(context)
    if not llm_configured():
        return {"summary": local, "source": "local"}
    system = (
        "You are a senior security consultant. Write a crisp executive summary (max 8 sentences) "
        "of the following external attack-surface assessment. Lead with overall posture, name the "
        "2-3 most urgent issues (KEV / high EPSS first), then one clear next action for each. "
        "Only use the data provided; never invent figures."
    )
    reply = await _chat(system, json.dumps(context))
    if not reply:
        return {"summary": local, "source": "local"}
    return {"summary": unredact(reply.strip(), mapping), "source": "llm"}


def local_summary(context: dict) -> str:
    sev = context.get("severity_counts", {})
    crit, high = sev.get("critical", 0), sev.get("high", 0)
    kev = sum(1 for f in context.get("findings", []) if f.get("kev"))
    avg = context.get("risk_summary", {}).get("average", 0)
    lines = [
        f"The assessment of {context.get('target') or 'the project'} discovered {context.get('assets_total', 0)} "
        f"assets ({context.get('live_assets', 0)} live) exposing {context.get('open_ports', 0)} open ports.",
        f"{crit} critical and {high} high severity findings were identified"
        + (f", including {kev} known-exploited (CISA KEV) issues." if kev else "."),
        f"Average weighted risk score: {avg}/100.",
    ]
    top = context.get("risk_summary", {}).get("top_assets") or []
    if top:
        worst = top[0]
        lines.append(f"Highest-risk asset: {worst.get('asset')} (score {worst.get('score')}, {worst.get('level')}).")
    if context.get("expired_certificates"):
        lines.append(f"Expired certificates: {', '.join(context['expired_certificates'])} — renew immediately.")
    if context.get("high_risk_ports"):
        lines.append(f"Reduce exposure of administrative ports: {', '.join(str(p) for p in context['high_risk_ports'][:8])}.")
    return " ".join(lines)


async def answer_question(db, scan_id: str, question: str) -> dict:
    context, mapping = await build_context(db, scan_id)
    ql = (question or "").lower()
    if not llm_configured():
        return {"answer": local_answer(context, question), "source": "local"}
    system = (
        "You are CyberSight ASM copilot, a security analyst assistant. Answer strictly grounded "
        "in the provided assessment context (JSON). If the data does not contain the answer, say "
        "so plainly. Be concise (max 6 sentences). Assets are labeled ASSET-n."
    )
    reply = await _chat(system, f"CONTEXT:\n{json.dumps(context)}\n\nQUESTION: {question}")
    if not reply:
        return {"answer": local_answer(context, question), "source": "local"}
    return {"answer": unredact(reply.strip(), mapping), "source": "llm"}


def local_answer(context: dict, question: str) -> str:
    ql = (question or "").lower()
    sev = context.get("severity_counts", {})
    if "critical" in ql or "urgent" in ql or "first" in ql or "priorit" in ql:
        urgents = [f for f in context.get("findings", [])
                   if f.get("kev") or (f.get("epss_percent") or 0) >= 50 or f.get("severity") in ("critical", "high")]
        names = ", ".join(f.get("finding") for f in urgents[:3]) or "none recorded"
        return (f"Patch first: {names}. There are {sev.get('critical', 0)} critical and {sev.get('high', 0)} "
                f"high findings across {context.get('live_assets', 0)} live assets.")
    if "kev" in ql or "exploited" in ql:
        kev = [f.get("finding") for f in context.get("findings", []) if f.get("kev")]
        return f"Known-exploited (KEV) findings: {', '.join(kev) if kev else 'none recorded'}."
    if "port" in ql or "expose" in ql:
        ports = context.get("high_risk_ports") or []
        return (f"{context.get('open_ports', 0)} ports are open; administrative services detected on: "
                f"{', '.join(str(p) for p in ports[:8]) if ports else 'none noted'}.")
    if "risk" in ql or "score" in ql or "posture" in ql:
        return (f"Average weighted risk is {context.get('risk_summary', {}).get('average', 0)}/100 across "
                f"{context.get('assets_total', 0)} assets. Top asset: "
                f"{(context.get('risk_summary', {}).get('top_assets') or [{}])[0].get('asset', 'n/a')}.")
    return ("LLM is not configured — answer limited to aggregate data: "
            f"{context.get('assets_total', 0)} assets, {sum(sev.values())} findings "
            f"({sev.get('critical', 0)} critical). Configure LLM_API_KEY for full AI analysis.")
