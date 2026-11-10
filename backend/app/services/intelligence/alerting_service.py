"""Outbound alerting: posts digest of new high-severity notifications to a
Slack-compatible webhook. Optional — disabled unless ALERT_WEBHOOK_URL is set.
"""

import logging
from datetime import datetime

from bson import ObjectId

from app.config import get_settings

logger = logging.getLogger(__name__)

_WEIGHT = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}


def configured() -> bool:
    return bool(get_settings().ALERT_WEBHOOK_URL)


def _passes(severity: str | None) -> bool:
    threshold = _WEIGHT.get(get_settings().ALERT_MIN_SEVERITY or "High", 1)
    return _WEIGHT.get(str(severity or "Info").title(), 4) <= threshold


async def dispatch_notifications(db, scan_id: str, notifications: list[dict]) -> int:
    """Fire-and-forget webhook dispatch of qualifying notifications."""
    url = get_settings().ALERT_WEBHOOK_URL
    if not url or not notifications:
        return 0
    selected = [n for n in notifications if _passes(n.get("severity"))]
    if not selected:
        return 0
    selected.sort(key=lambda n: _WEIGHT.get(str(n.get("severity") or "Info").title(), 4))
    lines = [f"*{n.get('severity', 'Info')}* — {n.get('title', '')}: {(n.get('description') or '')[:180]}"
             for n in selected[:12]]
    payload = {
        "text": f"🛡 CyberSight ASM — {len(selected)} new alert(s) from scan {scan_id}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"🛡 CyberSight ASM — {len(selected)} new alert(s)"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}},
        ],
    }
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
        ok = response.status_code in (200, 201, 204)
        level = "info" if ok else "warning"
        await db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$push": {"logs": {"message": f"Webhook alert dispatch {'succeeded' if ok else f'failed ({response.status_code})'}",
                                 "timestamp": datetime.utcnow(), "level": level}}},
        )
        return len(selected) if ok else 0
    except Exception:
        logger.exception("Webhook dispatch failed for scan %s", scan_id)
        return 0
