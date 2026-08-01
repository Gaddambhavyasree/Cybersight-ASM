import asyncio
import logging
from datetime import datetime

from bson import ObjectId
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)
DKIM_SELECTORS = ("default", "selector1", "selector2", "google", "mail", "k1")
LOOKUP_TYPES = ("A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "CAA")


def _lookup(hostname: str, ip: str | None = None) -> list[dict]:
    """Blocking dnspython lookup. It is always called in a worker thread."""
    import dns.exception
    import dns.resolver
    import dns.reversename

    hostname = (hostname or "").strip().rstrip(".")
    if not hostname:
        return []
    resolver = dns.resolver.Resolver()
    resolver.timeout = 2.0
    resolver.lifetime = 4.0
    records: list[dict] = []

    def query(name: str, rtype: str, stored_type: str | None = None):
        try:
            answer = resolver.resolve(name, rtype, raise_on_no_answer=False)
            if not answer.rrset:
                return
            ttl = int(answer.rrset.ttl)
            for item in answer:
                value = item.to_text().strip()
                if rtype == "TXT":
                    value = value.replace('" "', '').strip('"')
                else:
                    value = value.rstrip(".")
                if value:
                    records.append({"record_type": stored_type or rtype, "record_value": value, "ttl": ttl})
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
            return
        except Exception:
            logger.debug("DNS %s lookup failed for %s", rtype, name, exc_info=True)

    for rtype in LOOKUP_TYPES:
        query(hostname, rtype)

    # Keep the original TXT record and expose well-known policy records explicitly.
    for item in list(records):
        if item["record_type"] == "TXT" and item["record_value"].lower().startswith("v=spf1"):
            item["record_type"] = "SPF"
            records.append({**item, "record_type": "TXT"})
    query(f"_dmarc.{hostname}", "TXT", "DMARC")
    for selector in DKIM_SELECTORS:
        query(f"{selector}._domainkey.{hostname}", "TXT", "DKIM")

    # PTR is meaningful for an IP. If the asset has no IP, use addresses found above.
    addresses = [ip] if ip else [r["record_value"] for r in records if r["record_type"] in ("A", "AAAA")]
    for address in addresses:
        try:
            query(dns.reversename.from_address(address).to_text(), "PTR")
        except Exception:
            continue
    return records


class DNSIntelligenceExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.DNS_INTELLIGENCE, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        try:
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan:
                return self._error("Scan record not found for DNS Intelligence")
            project_id = str(scan.get("project_id", ""))
            assets = await db.assets.find({"project_id": project_id}).to_list(length=None)
            await self._logs(db, scan_id, [log_event("DNS Intelligence started"), log_event(f"Scanning {len(assets)} discovered assets")])
            saved = 0
            for asset in assets:
                try:
                    saved += await self._asset(db, scan_id, project_id, asset)
                except Exception as exc:
                    await self._log(db, scan_id, f"DNS lookup failed for {asset.get('hostname', 'unknown')}: {type(exc).__name__}", "warning")
            await self._logs(db, scan_id, [log_event(f"Saved {saved} DNS records"), log_event("DNS Intelligence completed")])
            return {"status": "success", "stage": self.stage.value, "message": f"Saved {saved} DNS records", "data": {"total": saved, "assets_scanned": len(assets)}}
        except Exception as exc:
            logger.exception("[%s] DNS Intelligence failed", scan_id)
            try:
                await self._log(db, scan_id, f"DNS Intelligence failed: {type(exc).__name__}: {exc}", "error")
            except Exception:
                pass
            # A stage-level infrastructure failure is reported, but execute always returns.
            return self._error(f"DNS Intelligence failed: {type(exc).__name__}: {exc}")

    async def _asset(self, db, scan_id: str, project_id: str, asset: dict) -> int:
        hostname = (asset.get("hostname") or "").strip().rstrip(".")
        await self._log(db, scan_id, f"Resolving {hostname}")
        try:
            records = await asyncio.wait_for(asyncio.to_thread(_lookup, hostname, asset.get("ip")), timeout=30)
        except Exception as exc:
            await self._log(db, scan_id, f"DNS lookup failed for {hostname}: {type(exc).__name__}", "warning")
            records = []
        now = datetime.utcnow()
        asset_id = str(asset.get("_id"))
        for record in records:
            await db.dns_records.update_one(
                {"project_id": project_id, "asset_id": asset_id, "record_type": record["record_type"], "record_value": record["record_value"]},
                {"$setOnInsert": {"first_seen": now, "created_at": now}, "$set": {"scan_id": scan_id, "hostname": hostname, "ttl": record.get("ttl"), "source": "dnspython", "last_seen": now, "updated_at": now}},
                upsert=True,
            )
            await self._log(db, scan_id, f"{record['record_type']} Record found for {hostname}")
        values = {rtype: [r["record_value"] for r in records if r["record_type"] == rtype] for rtype in ("MX", "TXT", "NS")}
        spf = next((r["record_value"] for r in records if r["record_type"] == "SPF"), None)
        dmarc = next((r["record_value"] for r in records if r["record_type"] == "DMARC"), None)
        dkim = [r["record_value"] for r in records if r["record_type"] == "DKIM"]
        count = await db.dns_records.count_documents({"project_id": project_id, "asset_id": asset_id})
        await db.assets.update_one({"_id": asset.get("_id")}, {"$set": {"dns_records_count": count, "dns_last_scan": now, "mx_records": values["MX"], "txt_records": values["TXT"], "ns_records": values["NS"], "spf": spf, "dmarc": dmarc, "dkim": dkim, "updated_at": now}})
        return len(records)

    async def _log(self, db, scan_id, message, level="info"):
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": log_event(message, level)}})

    async def _logs(self, db, scan_id, entries):
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"$each": entries}}})

    def _error(self, message):
        return {"status": "error", "stage": self.stage.value, "message": message}
