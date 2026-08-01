import asyncio, logging
from datetime import datetime
from bson import ObjectId
from pymongo import UpdateOne
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event
from app.config import get_settings

logger = logging.getLogger(__name__)
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

class ThreatIntelligenceExecutor(BaseStageExecutor):
    def __init__(self): super().__init__(stage=ScanStage.THREAT_INTELLIGENCE, simulated_delay=0)
    async def _request(self, client, url, headers=None, params=None):
        for attempt in range(2):
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code in (429, 500, 502, 503, 504): await asyncio.sleep(2 ** attempt); continue
                if response.status_code in (403, 404): return None
                response.raise_for_status(); return response.json()
            except Exception:
                if attempt == 1: logger.warning("Threat provider request failed: %s", url)
                else: await asyncio.sleep(2 ** attempt)
        return None
    async def execute(self, scan_id, target, db):
        try:
            import httpx
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan: return self._error("Scan record not found for Threat Intelligence")
            project_id = str(scan.get("project_id", ""))
            # Shodan can contain intelligence for hosts that live-host
            # verification could not reach, so include every discovered asset
            # with an IP address as well as assets marked live.
            assets = await db.assets.find({"project_id": project_id, "$or": [{"is_live": True}, {"ip": {"$exists": True, "$nin": [None, ""]}}]}).to_list(None)
            vulns = await db.vulnerabilities.find({"project_id": project_id, "scan_id": scan_id}).to_list(None)
            await self._logs(db, scan_id, [log_event("Threat Intelligence started"), log_event(f"Enriching {len(assets)} live assets")])
            settings = get_settings(); timeout = httpx.Timeout(8.0, connect=3.0); now = datetime.utcnow()
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                # Provider outages and rate limits must not fail the scan. Run asset
                # enrichment concurrently with a small bound to keep scans responsive.
                try:
                    await asyncio.wait_for(self._asset_phase(client, db, scan_id, project_id, assets, settings, now), timeout=120)
                except Exception:
                    logger.exception("Asset threat enrichment failed; continuing scan")
                    await self._log(db, scan_id, "Asset threat enrichment failed; scan continued", "warning")
                try:
                    await asyncio.wait_for(self._vulnerability_phase(client, db, scan_id, project_id, vulns, settings, now), timeout=120)
                except Exception:
                    logger.exception("Vulnerability threat enrichment failed; continuing scan")
                    await self._log(db, scan_id, "Vulnerability threat enrichment failed; scan continued", "warning")
            await self._log(db, scan_id, "Threat Intelligence completed")
            return {"status": "success", "stage": self.stage.value, "message": f"Enriched {len(assets)} assets and {len(vulns)} vulnerabilities", "data": {"assets": len(assets), "vulnerabilities": len(vulns)}}
        except Exception as exc:
            logger.exception("Threat Intelligence failed")
            return self._error(f"Threat Intelligence failed: {type(exc).__name__}: {exc}")
    async def _asset_phase(self, client, db, scan_id, project_id, assets, settings, now):
        semaphore = asyncio.Semaphore(4)
        async def enrich(asset):
            async with semaphore:
                await self._enrich_asset(client, db, scan_id, project_id, asset, settings, now)
        await asyncio.gather(*(enrich(asset) for asset in assets), return_exceptions=True)

    async def _enrich_asset(self, client, db, scan_id, project_id, asset, settings, now):
            ip = asset.get("ip"); host = asset.get("hostname", "")
            shodan = None
            if settings.SHODAN_API_KEY and ip:
                await self._log(db, scan_id, f"Querying Shodan for {ip}")
                shodan = await self._request(client, f"https://api.shodan.io/shodan/host/{ip}", params={"key": settings.SHODAN_API_KEY})
                if shodan:
                    await db.assets.update_one({"_id": asset["_id"]}, {"$set": {"asn": shodan.get("asn"), "isp": shodan.get("isp"), "organization": shodan.get("org"), "country": shodan.get("country_name"), "city": shodan.get("city"), "os": shodan.get("os"), "hostnames": shodan.get("hostnames", []), "shodan_last_update": now}})
                await self._log(db, scan_id, "Shodan enrichment completed" if shodan else f"Shodan enrichment failed for {ip}", "info" if shodan else "warning")
            elif not settings.SHODAN_API_KEY: await self._log(db, scan_id, "Shodan API key missing; skipped enrichment", "warning")
            vt = None
            if settings.VT_API_KEY and (ip or host):
                target = ip or host; await self._log(db, scan_id, f"Querying VirusTotal for {target}"); endpoint = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}" if ip else f"https://www.virustotal.com/api/v3/domains/{host}"
                vt = await self._request(client, endpoint, headers={"x-apikey": settings.VT_API_KEY}); await self._log(db, scan_id, "VirusTotal enrichment completed" if vt else f"VirusTotal enrichment failed for {target}", "info" if vt else "warning")
            elif not settings.VT_API_KEY: await self._log(db, scan_id, "VirusTotal API key missing; skipped enrichment", "warning")
            queried_shodan = bool(settings.SHODAN_API_KEY and ip)
            queried_vt = bool(settings.VT_API_KEY and (ip or host))
            if shodan or vt or queried_shodan or queried_vt:
                source = ",".join(x for x, present in (("shodan", queried_shodan), ("virustotal", queried_vt)) if present)
                await db.threat_intelligence.update_one({"project_id": project_id, "vulnerability_id": f"asset:{asset['_id']}"}, {"$set": {"project_id": project_id, "scan_id": scan_id, "asset_id": str(asset["_id"]), "hostname": host, "ip": ip, "source": source, "shodan": shodan or {}, "virustotal": vt or {}, "updated_at": now}, "$setOnInsert": {"vulnerability_id": f"asset:{asset['_id']}", "created_at": now}}, upsert=True)
    async def _vulnerability_phase(self, client, db, scan_id, project_id, vulns, settings, now):
        if not vulns: await self._log(db, scan_id, "No vulnerabilities to enrich"); return
        await self._log(db, scan_id, f"Enriching {len(vulns)} vulnerabilities"); kev_data = await self._request(client, KEV_URL); kev_map = {x.get("cveID"): x for x in (kev_data or {}).get("vulnerabilities", []) if isinstance(x, dict) and x.get("cveID")}; cache = {}; ops = []
        for vuln in vulns:
            cve = vuln.get("cve"); nvd = None
            if cve and settings.NVD_API_KEY:
                await self._log(db, scan_id, f"Querying NVD for {cve}"); cache[cve] = cache.get(cve) or await self._request(client, "https://services.nvd.nist.gov/rest/json/cves/2.0", headers={"apiKey": settings.NVD_API_KEY}, params={"cveId": cve}); raw = (cache[cve] or {}).get("vulnerabilities", []); nvd = raw[0].get("cve") if raw and isinstance(raw[0], dict) else None
            kev = kev_map.get(cve); metrics = {}; desc = vuln.get("description"); refs = vuln.get("references") or []; cwe = vuln.get("cwe"); cvss = vuln.get("cvss")
            if nvd:
                desc = next((x.get("value") for x in nvd.get("descriptions", []) if x.get("lang") == "en"), desc); refs = [x.get("url") for x in nvd.get("references", []) if x.get("url")] or refs; metrics = ((nvd.get("metrics", {}).get("cvssMetricV31") or nvd.get("metrics", {}).get("cvssMetricV30") or [{}])[0].get("cvssData", {})); cvss = cvss or metrics.get("baseScore"); cwe = cwe or next((x.get("value") for x in nvd.get("weaknesses", [{}])[0].get("description", []) if x.get("value")), None)
            update = {"description": desc, "cvss": cvss, "cwe": cwe, "references": refs, "attack_vector": metrics.get("attackVector"), "attack_complexity": metrics.get("attackComplexity"), "kev": bool(kev), "last_enriched": now}; await db.vulnerabilities.update_one({"_id": vuln["_id"]}, {"$set": update})
            doc = {"project_id": project_id, "scan_id": scan_id, "asset_id": vuln.get("asset_id"), "vulnerability_id": str(vuln["_id"]), "hostname": vuln.get("hostname"), "url": vuln.get("url"), "cve": cve, "source": "nvd,cisa" if nvd or kev else "local", "severity": vuln.get("severity"), **update, "published": nvd.get("published") if nvd else None, "last_modified": nvd.get("lastModified") if nvd else None, "kev_vendor": kev.get("vendorProject") if kev else None, "kev_product": kev.get("product") if kev else None, "kev_due_date": kev.get("dueDate") if kev else None, "updated_at": now}; ops.append(UpdateOne({"project_id": project_id, "vulnerability_id": str(vuln["_id"])}, {"$set": doc, "$setOnInsert": {"created_at": now}}, upsert=True))
        if ops: await db.threat_intelligence.bulk_write(ops, ordered=False)
    async def _log(self, db, sid, msg, level="info"): await db.scans.update_one({"_id": ObjectId(sid)}, {"$push": {"logs": log_event(msg, level)}})
    async def _logs(self, db, sid, entries): await db.scans.update_one({"_id": ObjectId(sid)}, {"$push": {"logs": {"$each": entries}}})
    def _error(self, message): return {"status": "error", "stage": self.stage.value, "message": message}
