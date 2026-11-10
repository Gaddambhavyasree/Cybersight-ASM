"""Live stack verification: connect exactly as app startup does (read-only + indexes)."""
import asyncio, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from app.database import connect_to_database, close_database_connection, get_database
    from app.config import get_settings

    s = get_settings()
    print("Atlas endpoint:", s.MONGODB_URL.split("@")[-1].split("/")[0], "| database:", s.DATABASE_NAME)
    await connect_to_database()
    db = get_database()
    ping = await db.command("ping")
    print("Atlas ping:", ping.get("ok"))

    expected = ["users", "projects", "scans", "assets", "ports", "technologies", "dns_records",
                "ssl_analysis", "web_assets", "vulnerabilities", "threat_intelligence",
                "scan_history", "reports", "notifications", "global_settings", "user_settings", "api_keys"]
    info = {name: await db[name].count_documents({}) for name in expected}
    print("Collection counts:")
    for k, v in info.items():
        print(f"  {k:20s} {v}")
    if info["assets"]:
        sample = await db.assets.find_one({"business_context": {"$exists": True}})
        print("Asset context tagging in use:", bool(sample))
    if info["vulnerabilities"]:
        with_epss = await db.vulnerabilities.count_documents({"epss": {"$exists": True, "$ne": None}})
        kev = await db.vulnerabilities.count_documents({"kev": True})
        print(f"EPSS-enriched vulns: {with_epss} | KEV-flagged: {kev}")
    started = await db.scans.find_one({"scan_name": {"$regex": "Continuous monitor", "$options": "i"}})
    print("Scheduler-generated scans found:", bool(started))
    close = await client_test()
    await close_database_connection()
    print("LIVE DB CHECK OK")

async def client_test():
    return None

if __name__ == "__main__":
    asyncio.run(main())
