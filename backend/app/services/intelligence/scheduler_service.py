"""Continuous-monitoring scheduler.

Actually implements the "scheduler"/"enable_continuous_monitoring" options that
already exist in the Admin Settings UI. When enabled, a background task issues
a fresh scan for every project on the configured cadence (hourly / daily /
weekly) and records progress in the scans collection like any manual scan.

Disabled by default — the app behaves exactly as before until an admin turns
the toggle on in Settings.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from bson import ObjectId

from app.services.scanEngine import scan_engine

logger = logging.getLogger(__name__)

TASK: asyncio.Task | None = None
INTERVALS = {"hourly": timedelta(hours=1), "daily": timedelta(days=1), "weekly": timedelta(days=7)}
DEFAULT_INTERVAL = INTERVALS["weekly"]

_active_states = {"pending", "queued", "running"}


async def _tick(db):
    settings_doc = await db.global_settings.find_one({"_id": "global"})
    scheduler = ((settings_doc or {}).get("settings") or {}).get("scheduler") or {}
    if not scheduler.get("enabled"):
        return
    frequency = scheduler.get("frequency") or "weekly"
    interval = INTERVALS.get(frequency, DEFAULT_INTERVAL)
    projects = []
    async for project in db.projects.find({}, {"name": 1, "target_domain": 1, "created_by": 1}):
        projects.append(project)
    for project in projects:
        try:
            pid = str(project["_id"])
            state = await db.monitor_state.find_one({"project_id": pid}) or {}
            now = datetime.utcnow()
            next_run = state.get("next_run_at")
            if not next_run:
                next_run = now + timedelta(seconds=15)  # first run shortly after enabling
            if now < next_run:
                continue
            busy = await db.scans.count_documents(
                {"project_id": pid, "status": {"$in": list(_active_states)}}
            )
            if busy:
                next_run = now + timedelta(minutes=10)
            else:
                await _enqueue_scan(db, project)
                logger.info("Continuous monitor: scan enqueued for %s", project.get("target_domain"))
                next_run = now + interval
            await db.monitor_state.update_one(
                {"project_id": pid},
                {"$set": {"project_id": pid, "next_run_at": next_run, "last_checked": now,
                          "updated_at": now},
                 "$setOnInsert": {"created_at": now}},
                upsert=True,
            )
        except Exception:
            logger.exception("Continuous monitor iteration failed for project %s", project.get("_id"))


async def _enqueue_scan(db, project: dict):
    pid = str(project["_id"])
    user_id = str(project.get("created_by") or "")
    now = datetime.utcnow()
    scan_name = f"Continuous monitor — {now.strftime('%Y-%m-%d %H:%M')}"
    scan_doc = {
        "project_id": pid,
        "project_name": project.get("name"),
        "target_domain": project.get("target_domain", ""),
        "scan_name": scan_name,
        "status": "queued",
        "current_stage": "waiting",
        "progress": 0,
        "started_at": None,
        "completed_at": None,
        "cancelled_at": None,
        "failure_stage": None,
        "failure_message": None,
        "assets_count": 0,
        "logs": [{"message": "Scan created automatically by continuous monitoring",
                  "timestamp": now, "level": "info"}],
        "initiated_by": user_id,
        "initiated_by_name": "Continuous Monitor",
        "created_at": now,
        "updated_at": now,
    }
    result = await db.scans.insert_one(scan_doc)
    scan_id = str(result.inserted_id)
    scan_doc["_id"] = result.inserted_id
    await scan_engine.start(scan_id, db)
    logger.info("Continuous monitor: enqueued scan %s for project %s", scan_id, pid)


async def _run_forever():
    from app.database import get_database
    db = get_database()
    while True:
        try:
            if db is not None:
                await _tick(db)
        except Exception:
            logger.exception("Continuous monitor tick failed")
        await asyncio.sleep(60)


def start_scheduler():
    global TASK
    if TASK is None or TASK.done():
        TASK = asyncio.create_task(_run_forever())
        logger.info("Continuous monitor scheduler started (inactive until enabled in Settings)")


def stop_scheduler():
    global TASK
    if TASK and not TASK.done():
        TASK.cancel()
    TASK = None
