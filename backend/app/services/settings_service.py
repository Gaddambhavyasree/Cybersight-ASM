from datetime import datetime
from fastapi import HTTPException

GLOBAL_DEFAULTS = {
    "general": {"organization_name": "", "application_name": "CyberSight ASM", "timezone": "UTC", "date_format": "YYYY-MM-DD", "language": "en", "theme": "system"},
    "scan": {"max_concurrent_scans": 2, "max_assets_per_scan": 1000, "scan_timeout": 3600, "httpx_timeout": 30, "naabu_timeout": 300, "katana_timeout": 300, "nuclei_timeout": 900, "retry_count": 2, "auto_save_results": True, "enable_scan_logs": True, "enable_historical_snapshots": True, "enable_continuous_monitoring": False, "default_scan_profile": "standard"},
    "scheduler": {"enabled": False, "frequency": "weekly", "cron_expression": "", "max_parallel_jobs": 1, "auto_reports": False, "auto_risk": True, "auto_threat_intelligence": True, "auto_notifications": True},
    "integrations": {"shodan": {"configured": False}, "virustotal": {"configured": False}, "nvd": {"configured": False}, "cisa": {"configured": False}},
    "notifications": {"enabled": True, "severity_threshold": "Info", "new_asset": True, "asset_removed": True, "new_port": True, "critical_vulnerability": True, "ssl_expiration": True, "threat_intelligence": True, "risk_changes": True, "scan_completion": True},
    "reports": {"default_type": "executive", "company_name": "", "footer_text": "", "include_charts": True, "include_recommendations": True, "pdf_layout": "standard"},
    "security": {"jwt_expiration_minutes": 60, "min_password_length": 8, "require_uppercase": True, "require_numbers": True, "require_special": True, "session_timeout_minutes": 60, "max_login_attempts": 5, "lockout_minutes": 15},
    "audit": {"enabled": True, "log_scan_activity": True, "log_user_activity": True, "log_settings_changes": True, "log_login_events": True, "retention_days": 365},
}
USER_DEFAULTS = {"theme": "system", "dashboard_layout": "default", "rows_per_table": 25, "default_landing_page": "dashboard", "notification_sound": True, "timezone": "UTC", "notification_preferences": {}}

def merge(defaults, saved):
    out = dict(defaults)
    for k, v in (saved or {}).items(): out[k] = merge(v, out.get(k, {})) if isinstance(v, dict) else v
    return out

def _admin(user):
    if str(user.get("role", "")).lower() != "admin": raise HTTPException(403, "Administrator access required")

async def get_global(db):
    doc = await db.global_settings.find_one({"_id": "global"})
    settings = merge(GLOBAL_DEFAULTS, (doc or {}).get("settings", {}));
    # Never return secret material; expose only configured state and masked values.
    # Integration status for environment-configured providers is overlaid here so
    # the admin UI reflects reality without storing secrets in the database.
    from app.config import get_settings
    s = get_settings()
    integrations = settings.setdefault("integrations", {})
    integrations.setdefault("llm", {})["configured"] = bool(s.LLM_API_KEY)
    integrations.setdefault("jira", {})["configured"] = bool(s.JIRA_URL and s.JIRA_EMAIL and s.JIRA_API_TOKEN and s.JIRA_PROJECT_KEY)
    integrations.setdefault("thehive", {})["configured"] = bool(s.THEHIVE_URL and s.THEHIVE_API_KEY)
    integrations.setdefault("alert_webhook", {})["configured"] = bool(s.ALERT_WEBHOOK_URL)
    return {"settings": settings}

async def update_global(db, user, payload):
    _admin(user); current = await db.global_settings.find_one({"_id": "global"}) or {}; settings = merge(GLOBAL_DEFAULTS, current.get("settings", {})); incoming = payload.get("settings", {})
    for key, value in incoming.items():
        if key in GLOBAL_DEFAULTS: settings[key] = merge(settings.get(key, {}), value) if isinstance(value, dict) else value
    # Keys are stored separately and are never included in responses.
    for provider in ("shodan", "virustotal", "nvd", "cisa"):
        key = incoming.get("integrations", {}).get(provider, {}).get("api_key") if isinstance(incoming.get("integrations", {}).get(provider), dict) else None
        if key: await db.api_keys.update_one({"provider": provider}, {"$set": {"provider": provider, "api_key": key, "updated_at": datetime.utcnow(), "updated_by": str(user["_id"]) }}, upsert=True); settings["integrations"].setdefault(provider, {})["configured"] = True
        settings["integrations"].setdefault(provider, {}).pop("api_key", None)
    await db.global_settings.update_one({"_id": "global"}, {"$set": {"settings": settings, "updated_at": datetime.utcnow(), "updated_by": str(user["_id"])}}, upsert=True)
    return {"settings": settings}

async def get_user(db, user):
    doc = await db.user_settings.find_one({"user_id": str(user["_id"])})
    return {"settings": merge(USER_DEFAULTS, (doc or {}).get("settings", {}))}

async def update_user(db, user, payload):
    settings = merge(USER_DEFAULTS, payload.get("settings", {})); await db.user_settings.update_one({"user_id": str(user["_id"])}, {"$set": {"settings": settings, "updated_at": datetime.utcnow()}}, upsert=True); return {"settings": settings}

async def test_connection(db, user, provider):
    _admin(user)
    if provider in ("shodan", "virustotal", "nvd", "cisa", "llm"):
        if provider == "llm":
            from app.config import get_settings
            key = get_settings().LLM_API_KEY
            return {"provider": provider, "status": "connected" if key else "not_configured", "last_tested": datetime.utcnow()}
        key = await db.api_keys.find_one({"provider": provider})
        return {"provider": provider, "status": "connected" if key and key.get("api_key") else "invalid_api_key", "last_tested": datetime.utcnow()}
    from app.config import get_settings
    from app.services.intelligence import ticketing_service
    s = get_settings()
    if provider == "jira":
        status = "connected" if ticketing_service.jira_configured() else "not_configured"
    elif provider == "thehive":
        status = "connected" if ticketing_service.thehive_configured() else "not_configured"
    elif provider == "alert_webhook":
        status = "connected" if s.ALERT_WEBHOOK_URL else "not_configured"
    else:
        raise HTTPException(400, "Unsupported integration")
    return {"provider": provider, "status": status, "last_tested": datetime.utcnow()}


async def get_api_key(db, provider: str, fallback: str = "") -> str:
    """Resolves provider credentials: Settings UI (database) wins, environment as fallback."""
    try:
        doc = await db.api_keys.find_one({"provider": provider})
        if doc and doc.get("api_key"):
            return doc["api_key"]
    except Exception:
        pass
    return fallback or ""
