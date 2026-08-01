import asyncio, json, logging, os, shutil, subprocess, traceback, sys
from datetime import datetime
from urllib.parse import urlparse
from bson import ObjectId
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)
SENSITIVE = ("admin", "administrator", "login", "signin", "dashboard", "panel", "console", "api", "graphql", "swagger", "openapi", "actuator", "jenkins", ".git", ".env", "config", "backup", "db", "phpmyadmin")

def _katana_path():
    for name in ("katana.exe", "katana"):
        p = shutil.which(name)
        if p and "python" not in p.lower(): return p
    for p in (os.path.expanduser(r"~\go\bin\katana.exe"), os.path.expanduser(r"~\tools\katana.exe")):
        if os.path.isfile(p): return p
    return None

def _parse(line, base_url):
    try: data = json.loads(line)
    except (json.JSONDecodeError, TypeError): return None
    if not isinstance(data, dict): return None
    request = data.get("request")
    request = request if isinstance(request, dict) else {}
    response = data.get("response")
    response = response if isinstance(response, dict) else {}
    # Katana versions differ: endpoint may be nested under request, or top-level.
    url = request.get("endpoint") or request.get("url") or data.get("endpoint") or data.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")): return None
    parsed = urlparse(url); path = parsed.path or "/"; query = parsed.query or None
    low = (path + ("?" + query if query else "")).lower(); reasons = [x for x in SENSITIVE if x in low]
    ext = path.lower().rsplit(".", 1)[-1] if "." in path.rsplit("/", 1)[-1] else ""
    resource = "javascript" if ext in ("js", "mjs") else "css" if ext == "css" else "image" if ext in ("png", "jpg", "jpeg", "gif", "svg", "webp", "ico") else "api" if any(x in low for x in ("/api", "graphql", "swagger", "openapi")) else "page"
    headers = response.get("headers")
    headers = headers if isinstance(headers, dict) else {}
    depth = data.get("depth", 0)
    if not isinstance(depth, int): depth = 0
    return {"url": url, "base_url": base_url, "path": path, "query": query, "method": request.get("method") if isinstance(request.get("method"), str) else "GET", "status_code": response.get("status_code") or data.get("status_code"), "content_type": headers.get("content-type") or headers.get("Content-Type"), "resource_type": resource, "depth": depth, "title": response.get("title") or data.get("title"), "is_sensitive": bool(reasons), "sensitive_reason": ", ".join(reasons) if reasons else None}

def _run(path, url):
    cmd = [path, "-u", url, "-silent", "-jsonl", "-d", "3", "-timeout", "10", "-no-color"]
    p = None
    try:
        flags = (subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0) | (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags)
        stdout, stderr = p.communicate(timeout=75)
        if p.returncode not in (0, None): logger.warning("Katana exited with code %s for %s: %s", p.returncode, url, stderr.strip())
        rows = []
        for line in stdout.splitlines():
            row = _parse(line, url)
            if row is not None: rows.append(row)
        return rows
    except subprocess.TimeoutExpired:
        logger.warning("Katana timed out for %s", url)
        if p is not None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, timeout=5)
            else:
                p.kill()
            try: p.communicate(timeout=5)
            except Exception: pass
        return []
    except Exception:
        logger.exception("Katana execution failed for %s", url)
        if p is not None and p.poll() is None:
            if os.name == "nt": subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, timeout=5)
            else: p.kill()
        return []

class WebCrawlingExecutor(BaseStageExecutor):
    def __init__(self): super().__init__(stage=ScanStage.WEB_CRAWLING, simulated_delay=0)
    async def execute(self, scan_id, target, db):
        try:
            path = _katana_path()
            if not path: return self._error("Katana executable not found")
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan: return self._error("Scan record not found for Web Crawling")
            project_id = str(scan.get("project_id", "")); assets = await db.assets.find({"project_id": project_id, "scan_id": scan_id, "is_live": True}).to_list(None)
            await self._logs(db, scan_id, [log_event("Web Crawling started"), log_event(f"Crawling {len(assets)} live assets")]); saved = 0
            for asset in assets:
                host = asset.get("hostname", ""); base = asset.get("final_url") or ("https://" if asset.get("https_enabled") else "http://") + host
                try:
                    rows = await asyncio.wait_for(asyncio.to_thread(_run, path, base), timeout=90); now = datetime.utcnow(); js = api = admin = 0
                    for row in rows:
                        await db.web_assets.update_one({"project_id": project_id, "asset_id": str(asset["_id"]), "url": row["url"]}, {"$setOnInsert": {"first_seen": now, "created_at": now}, "$set": {**row, "project_id": project_id, "scan_id": scan_id, "asset_id": str(asset["_id"]), "hostname": host, "source": "katana", "last_seen": now, "updated_at": now}}, upsert=True)
                        js += row["resource_type"] == "javascript"; api += row["resource_type"] == "api"; admin += row["is_sensitive"] and any(x in (row["path"] or "").lower() for x in ("admin", "panel", "console"))
                    stored_count = await db.web_assets.count_documents({"project_id": project_id, "asset_id": str(asset["_id"])})
                    await db.assets.update_one({"_id": asset["_id"]}, {"$set": {"endpoint_count": stored_count, "javascript_files": js, "api_count": api, "admin_panels": admin, "crawl_last_scan": now, "updated_at": now}}); saved += stored_count; await self._log(db, scan_id, f"{host}: {stored_count} URLs discovered")
                except Exception as exc:
                    info = sys.exc_info(); tb = traceback.extract_tb(info[2])[-1] if info[2] else None
                    logger.error("Crawl failed for %s: type=%s file=%s line=%s\n%s", host, type(exc).__name__, tb.filename if tb else "unknown", tb.lineno if tb else "unknown", traceback.format_exc())
                    await self._log(db, scan_id, f"Crawl failed for {host}: {type(exc).__name__} ({tb.filename}:{tb.lineno})" if tb else f"Crawl failed for {host}: {type(exc).__name__}", "warning")
            await self._log(db, scan_id, f"Saved {saved} resources"); await self._log(db, scan_id, "Web Crawling completed")
            return {"status": "success", "stage": self.stage.value, "message": f"Saved {saved} resources", "data": {"total": saved}}
        except Exception as exc: logger.exception("Web crawling failed"); return self._error(f"Web Crawling failed: {type(exc).__name__}: {exc}")
    async def _log(self, db, scan_id, message, level="info"): await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": log_event(message, level)}})
    async def _logs(self, db, scan_id, entries): await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"$each": entries}}})
    def _error(self, message): return {"status": "error", "stage": self.stage.value, "message": message}
