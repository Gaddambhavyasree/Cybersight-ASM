"""Read-only: list projects + recent scans to pick a live-scan target."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from app.database import connect_to_database, close_database_connection, get_database
    from app.config import get_settings
    get_settings()
    await connect_to_database()
    db = get_database()
    print("Projects:")
    async for p in db.projects.find({}, {"name": 1, "target_domain": 1}).sort("created_at", -1):
        print(f"  {str(p['_id'])}  {p.get('name'):28s}  {p.get('target_domain')}")
    print("\nUsers (no secrets):")
    async for u in db.users.find({}, {"email": 1, "role": 1}):
        print(f"  {u.get('email'):40s} {u.get('role')}")
    print("\nLatest 5 scans:")
    async for s in db.scans.find({}, {"scan_name": 1, "target_domain": 1, "status": 1, "current_stage": 1}).sort("created_at", -1).limit(5):
        print(f"  {s.get('status'):10s} {s.get('scan_name','')[:24]:24s} {s.get('target_domain')}")
    await close_database_connection()

asyncio.run(main())
