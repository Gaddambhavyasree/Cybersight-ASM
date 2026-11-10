"""Diagnose why the vulnerability stage produced zero findings (read-only)."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from app.database import connect_to_database, close_database_connection, get_database
    from app.config import get_settings
    get_settings()
    await connect_to_database()
    db = get_database()

    stages = {}
    async for scan in db.scans.find({}, {"scan_name": 1, "status": 1, "failure_stage": 1,
                                         "failure_message": 1, "current_stage": 1,
                                         "created_at": 1}).sort("created_at", -1):
        key = f"{scan.get('stage_fail', '')}"
        stages.setdefault(f"{scan.get('failure_stage')}", 0)
        stages[f"{scan.get('failure_stage')}"] = stages.get(f"{scan.get('failure_stage')}", 0) + 1
        print(f"{scan.get('created_at').strftime('%Y-%m-%d %H:%M') if scan.get('created_at') else '?'} | {scan.get('status'):10s} | {scan.get('failure_stage') or scan.get('current_stage') or '?':24s} | {str(scan.get('failure_message') or '')[:80]}")
    print("\nFailure stage histogram:", stages)

    # Pull vulnerability-stage log lines from the 3 most recent scans
    async for scan in db.scans.find({}, {"logs": 1, "scan_name": 1}).sort("created_at", -1).limit(3):
        print("\n===", scan.get("scan_name"))
        hit = False
        for log in (scan.get("logs") or []):
            line = str(log.get("message", ""))
            if any(k in line.lower() for k in ("nuclei", "vulnerab", "katana", "crawling")):
                print(f"  [{log.get('level','i')}] {line[:130]}")
                hit = True
        if not hit:
            print("  (no vulnerability/crawling log lines found)")

    await close_database_connection()

asyncio.run(main())
