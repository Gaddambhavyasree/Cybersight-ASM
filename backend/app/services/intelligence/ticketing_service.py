"""Auto-ticketing for critical findings (Jira + TheHive).

Both integrations are optional and configuration-driven — with no credentials
configured the service is a no-op, so existing scan behavior is unchanged.

Environment variables:
    JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY
    THEHIVE_URL, THEHIVE_API_KEY, THEHIVE_ORG
"""

import logging
import re
from datetime import datetime

from bson import ObjectId

from app.config import get_settings

logger = logging.getLogger(__name__)

_KEY_CHARS = re.compile(r"[^A-Za-z0-9]")


def _finding_key(scan_id: str, vuln: dict) -> str:
    return _KEY_CHARS.sub("-", f"{scan_id}-{vuln.get('asset_id')}-{vuln.get('template_id') or vuln.get('cve') or 'finding'}")


def jira_configured() -> bool:
    s = get_settings()
    return bool(s.JIRA_URL and s.JIRA_EMAIL and s.JIRA_API_TOKEN and s.JIRA_PROJECT_KEY)


def thehive_configured() -> bool:
    s = get_settings()
    return bool(s.THEHIVE_URL and s.THEHIVE_API_KEY)


def configured() -> bool:
    return jira_configured() or thehive_configured()


def _title_for(vuln: dict, asset: dict) -> str:
    label = vuln.get("cve") or vuln.get("template_name") or "Security finding"
    host = (asset.get("hostname") or "")[:60]
    return f"[CyberSight {str(vuln.get('severity', 'high')).upper()}] {label} on {host}"


def _description_for(vuln: dict, asset: dict) -> str:
    lines = [
        f"Severity: {vuln.get('severity', 'unknown')}",
        f"CVSS: {vuln.get('cvss') or 'n/a'}",
        f"CVE: {vuln.get('cve') or 'n/a'}",
        f"Asset: {asset.get('hostname') or 'unknown'}",
        f"URL: {vuln.get('url') or 'n/a'}",
        "",
        "Detected automatically by CyberSight ASM during vulnerability assessment.",
    ]
    if vuln.get("kev"):
        lines.append("⚠ Listed in CISA KEV — actively exploited.")
    return "\n".join(lines)


async def _already_created(db, scan_id: str, finding_key: str) -> bool:
    return bool(await db.integration_tickets.find_one({"scan_id": scan_id, "finding_key": finding_key}))


async def _mark(db, scan_id: str, finding_key: str, target: str, external_id, status: str):
    await db.integration_tickets.update_one(
        {"scan_id": scan_id, "finding_key": finding_key, "target": target},
        {"$set": {"external_id": external_id, "status": status, "created_at": datetime.utcnow()}},
        upsert=True,
    )


async def _create_jira(client, settings, vuln: dict, asset: dict):
    payload = {
        "fields": {
            "project": {"key": settings.JIRA_PROJECT_KEY},
            "summary": _title_for(vuln, asset)[:250],
            "description": _description_for(vuln, asset)[:20000],
            "issuetype": {"name": "Task"},
            "labels": ["cybersight", f"cybersight-{vuln.get('severity', 'unknown')}"],
        }
    }
    response = await client.post(
        f"{settings.JIRA_URL.rstrip('/')}/rest/api/2/issue",
        auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN),
        json=payload,
    )
    if response.status_code in (200, 201):
        data = response.json()
        return data.get("key") or data.get("id")
    logger.warning("Jira issue creation failed (%s): %s", response.status_code, response.text[:300])
    return None


async def _create_thehive(client, settings, vuln: dict, asset: dict):
    payload = {
        "title": _title_for(vuln, asset)[:250],
        "description": _description_for(vuln, asset),
        "severity": {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(str(vuln.get("severity", "low")).lower(), 2),
        "type": "vulnerability",
        "tags": ["cybersight", f"{vuln.get('severity', 'unknown')}"],
    }
    if vuln.get("url"):
        payload["observable"] = [{"dataType": "url", "data": str(vuln["url"])[:250]}]
    headers = {"X-Api-Key": settings.THEHIVE_API_KEY, "Content-Type": "application/json"}
    if settings.THEHIVE_ORG:
        headers["X-Org"] = settings.THEHIVE_ORG
    response = await client.post(
        f"{settings.THEHIVE_URL.rstrip('/')}/api/case",
        headers=headers,
        json=payload,
    )
    if response.status_code in (200, 201):
        data = response.json()
        return data.get("_id") or data.get("id")
    logger.warning("TheHive case creation failed (%s): %s", response.status_code, response.text[:300])
    return None


async def auto_create_tickets(db, scan_id: str) -> int:
    """Create tickets for critical/high findings of a completed scan. Returns count."""
    s = get_settings()
    if not configured():
        return 0
    created = 0
    try:
        scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            return 0
        vulns = await db.vulnerabilities.find({
            "scan_id": scan_id,
            "severity": {"$in": ["critical", "high"]},
        }).to_list(50)
        if not vulns:
            return 0
        assets = {str(a["_id"]): a for a in await db.assets.find(
            {"project_id": str(scan.get("project_id"))}).to_list(1000)}

        import httpx
        timeout = httpx.Timeout(20.0, connect=8.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for vuln in vulns:
                key = _finding_key(scan_id, vuln)
                if await _already_created(db, scan_id, key):
                    continue
                asset = assets.get(str(vuln.get("asset_id") or ""), {})
                for name, enabled, creator in (
                    ("jira", jira_configured(), _create_jira),
                    ("thehive", thehive_configured(), _create_thehive),
                ):
                    if not enabled:
                        continue
                    try:
                        external = await creator(client, s, vuln, asset)
                        await _mark(db, scan_id, key, name, external or "?", "created" if external else "failed")
                        if external:
                            await db.scans.update_one(
                                {"_id": ObjectId(scan_id)},
                                {"$push": {"logs": {"message": f"Ticket created in {name.upper()}: {external}", "timestamp": datetime.utcnow(), "level": "info"}}},
                            )
                            created += 1
                    except Exception:
                        logger.exception("Ticketing integration %s failed for scan %s", name, scan_id)
        return created
    except Exception:
        logger.exception("Auto ticketing failed for scan %s", scan_id)
        return created
