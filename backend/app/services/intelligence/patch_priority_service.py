"""Risk-driven patching priorities.

Combines every open finding with what we know about the asset and the
exploitation landscape (CVSS, KEV, EPSS, exposure, business criticality) and
produces a ranked "patch these first" list instead of raw severity rows.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SEVERITY_BASE = {"critical": 40, "high": 30, "medium": 18, "low": 8, "info": 3}


def _num(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _clamp01(v): return max(0.0, min(1.0, float(v)))
def _noisy_or(rs):
    p=1.0
    for r in rs: p*=1.0-_clamp01(r)
    return 1.0-p

def score_finding(vuln: dict, asset: dict, intel: dict) -> tuple[int, dict]:
    base = SEVERITY_BASE.get(str(vuln.get("severity", "low")).lower(), 5)
    cvss = _num(vuln.get("cvss"))
    epss = _num(vuln.get("epss") or intel.get("epss"))
    kev = bool(vuln.get("kev") or intel.get("kev"))
    asset = asset or {}; intel = intel or {}; vuln = vuln or {}
    # normalised [0,1] components with relative weights as multipliers <=1
    comps = [
        ("severity", _clamp01(base/40.0)*0.9),
        ("cvss", _clamp01(cvss/10.0)*0.9),
        ("kev", (1.0 if kev else 0.0)*0.95),
        ("epss", _clamp01(epss)*0.9),
    ]
    live = bool(asset.get("is_live"))
    exposure_raw = (10 if live else 0)+(8 if _num(asset.get("admin_panels"))>0 else 0)+(5 if live and not asset.get("https_enabled") else 0)+(3 if live else 0)
    comps.append(("exposure", _clamp01(exposure_raw/26.0)*0.6))
    criticality = _num(asset.get("criticality"))
    comps.append(("business_criticality", _clamp01((criticality-1)/4.0 if criticality>1 else 0.0)*0.4))
    combined = _noisy_or([c for _,c in comps])
    score = int(round(_clamp01(combined)*100))
    parts = {k: round(c*100,1) for k,c in comps}
    return score, parts


def level(score: int) -> str:
    return "P1" if score >= 60 else "P2" if score >= 40 else "P3" if score >= 20 else "P4"


async def compute(db, user_project_ids: list[str], project_id: str | None = None, limit: int = 50):
    query_pid = project_id if project_id in user_project_ids else None
    if query_pid:
        vulns = await db.vulnerabilities.find({"project_id": query_pid}).limit(5000).to_list(5000)
    else:
        vulns = await db.vulnerabilities.find({"project_id": {"$in": user_project_ids}}).limit(5000).to_list(5000)

    generated_at = datetime.utcnow()
    if not vulns:
        return {"items": [], "patch_first": [], "summary": {
            "total_findings": 0, "kev_findings": 0, "high_epss": 0, "p1": 0, "p2": 0, "p3": 0, "p4": 0,
        }, "generated_at": generated_at}

    project_ids = list({str(v["project_id"]) for v in vulns})
    assets_by_id: dict[str, dict] = {}
    async for doc in db.assets.find({"project_id": {"$in": project_ids}}):
        assets_by_id[str(doc["_id"])] = doc

    # Threat-intelligence docs are keyed by vulnerability_id.
    intel_by_vid: dict[str, dict] = {}
    async for doc in db.threat_intelligence.find({"vulnerability_id": {"$type": "string"}, "epss": {"$exists": True}}):
        intel_by_vid[doc["vulnerability_id"]] = doc

    items = []
    counts = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}
    kev_count = epss_count = 0
    for vuln in vulns:
        vid = str(vuln["_id"])
        aid = str(vuln.get("asset_id") or "")
        asset = assets_by_id.get(aid, {})
        intel = intel_by_vid.get(vid, {})
        score, parts = score_finding(vuln, asset, intel)
        if intel.get("kev") or vuln.get("kev"):
            kev_count += 1
        if _num(vuln.get("epss") or intel.get("epss")) >= 0.4:
            epss_count += 1
        counts[level(score).lower()] += 1
        items.append({
            "vulnerability_id": vid,
            "asset_id": aid,
            "hostname": vuln.get("hostname") or asset.get("hostname") or "",
            "project_id": vuln.get("project_id"),
            "title": vuln.get("template_name") or vuln.get("cve") or "Finding",
            "cve": vuln.get("cve"),
            "template_id": vuln.get("template_id"),
            "severity": vuln.get("severity"),
            "cvss": vuln.get("cvss"),
            "epss": vuln.get("epss") or intel.get("epss"),
            "kev": bool(vuln.get("kev") or intel.get("kev")),
            "kev_due_date": intel.get("kev_due_date"),
            "priority_score": score,
            "priority_level": level(score),
            "score_breakdown": parts,
            "recommendation": recommendation(vuln, asset, intel),
        })

    items.sort(key=lambda x: x["priority_score"], reverse=True)
    return {
        "items": items[:limit],
        "patch_first": items[:12],
        "summary": {
            "total_findings": len(items),
            "kev_findings": kev_count,
            "high_epss": epss_count,
            **counts,
        },
        "generated_at": generated_at,
    }


def recommendation(vuln: dict, asset: dict, intel: dict) -> str:
    bits = []
    cve = vuln.get("cve")
    if cve:
        bits.append(f"Patch {cve} on {asset.get('hostname') or 'this asset'}")
    else:
        bits.append(f"Remediate '{vuln.get('template_name') or 'this finding'}' on {asset.get('hostname') or 'this asset'}")
    if intel.get("kev"):
        bits.append(f"actively exploited (KEV, due {intel.get('kev_due_date') or 'per CISA deadline'})")
    epss = _num(vuln.get("epss") or intel.get("epss"))
    if epss >= 0.5:
        bits.append(f"EPSS predicts {epss:.0%} chance of exploitation in the next 30 days")
    if not asset.get("https_enabled") and asset.get("is_live"):
        bits.append("service serves plaintext HTTP — restrict at the edge immediately")
    return " — ".join(bits)
