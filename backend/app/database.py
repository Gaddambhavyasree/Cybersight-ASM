from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
from pymongo.errors import DuplicateKeyError

settings = get_settings()

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_database():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    await db.users.create_index("email", unique=True)
    await db.users.create_index("verification_token")
    await db.users.create_index("reset_token")
    await db.projects.create_index("created_by")
    await db.projects.create_index([("created_by", 1), ("target_domain", 1)], unique=True)
    await db.projects.create_index("status")
    await db.projects.create_index("name")
    await db.scans.create_index("project_id")
    await db.scans.create_index("initiated_by")
    await db.scans.create_index("status")
    await db.scans.create_index("created_at")
    await db.scans.create_index("current_stage")
    await db.assets.create_index("project_id")
    await db.assets.create_index("scan_id")
    await db.assets.create_index("hostname")
    await db.assets.create_index("source")
    await db.assets.create_index("status")
    await db.assets.create_index([("project_id", 1), ("hostname", 1)], unique=True)
    await db.ports.create_index("project_id")
    await db.ports.create_index("scan_id")
    await db.ports.create_index("asset_id")
    await db.ports.create_index("hostname")
    await db.ports.create_index([("project_id", 1), ("asset_id", 1), ("port", 1), ("protocol", 1)], unique=True)
    await db.technologies.create_index("project_id")
    await db.technologies.create_index("asset_id")
    await db.technologies.create_index("technology_name")
    await db.dns_records.create_index("project_id")
    await db.dns_records.create_index("asset_id")
    await db.dns_records.create_index("scan_id")
    await db.dns_records.create_index("hostname")
    await db.dns_records.create_index("record_type")
    await db.ssl_analysis.create_index("project_id")
    await db.ssl_analysis.create_index("asset_id")
    await db.ssl_analysis.create_index("scan_id")
    await db.ssl_analysis.create_index("hostname")
    dns_key = [("project_id", 1), ("asset_id", 1), ("record_type", 1), ("record_value", 1)]
    async def ensure_unique(collection, key):
        try:
            await collection.create_index(key, unique=True)
            return
        except DuplicateKeyError:
            # Clean legacy duplicates before enforcing the constraint.
            groups = collection.aggregate([
                {"$group": {"_id": {field: f"${field}" for field, _ in key}, "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}},
            ])
            async for group in groups:
                await collection.delete_many({"_id": {"$in": group["ids"][1:]}})
            await collection.create_index(key, unique=True)

    await ensure_unique(db.technologies, [("project_id", 1), ("asset_id", 1), ("technology_name", 1), ("category", 1)])
    await ensure_unique(db.dns_records, dns_key)
    await ensure_unique(db.ssl_analysis, [("project_id", 1), ("asset_id", 1)])
    await db.web_assets.create_index("project_id")
    await db.web_assets.create_index("asset_id")
    await db.web_assets.create_index("scan_id")
    await db.web_assets.create_index("hostname")
    await db.web_assets.create_index("resource_type")
    await ensure_unique(db.web_assets, [("project_id", 1), ("asset_id", 1), ("url", 1)])
    await db.vulnerabilities.create_index("project_id")
    await db.vulnerabilities.create_index("scan_id")
    await db.vulnerabilities.create_index("asset_id")
    await db.vulnerabilities.create_index("severity")
    await ensure_unique(db.vulnerabilities, [("project_id", 1), ("asset_id", 1), ("url", 1), ("template_id", 1)])
    await db.threat_intelligence.create_index("project_id")
    await db.threat_intelligence.create_index("scan_id")
    await db.threat_intelligence.create_index("cve")
    await db.scan_history.create_index("scan_id", unique=True)
    await db.scan_history.create_index([("project_id", 1), ("completed_at", -1)])
    await db.reports.create_index([("generated_by", 1), ("generated_at", -1)])
    await db.reports.create_index([("project_id", 1), ("scan_id", 1)])
    await db.notifications.create_index([("project_id", 1), ("created_at", -1)])
    await db.notifications.create_index([("project_id", 1), ("status", 1)])
    await db.global_settings.create_index("updated_at")
    await db.user_settings.create_index("user_id", unique=True)
    await db.api_keys.create_index("provider", unique=True)
    await ensure_unique(db.threat_intelligence, [("project_id", 1), ("vulnerability_id", 1)])


async def close_database_connection():
    global client
    if client:
        client.close()


def get_database() -> AsyncIOMotorDatabase:
    return db
