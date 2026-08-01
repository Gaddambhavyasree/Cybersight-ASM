import asyncio
import logging
import socket
import ssl
from datetime import datetime, timezone

from bson import ObjectId
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)


def _analyse(hostname: str, ip: str | None = None) -> dict:
    """Perform one bounded TLS handshake and parse its peer certificate."""
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa

    address = ip or hostname
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1
    context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
    with socket.create_connection((address, 443), timeout=8) as raw:
        with context.wrap_socket(raw, server_hostname=hostname) as conn:
            cert_der = conn.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(cert_der)
            subject = cert.subject.rfc4514_string()
            issuer = cert.issuer.rfc4514_string()
            cn = next((x.value for x in cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)), None)
            try:
                san = [str(x.value) for x in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value]
            except x509.ExtensionNotFound:
                san = []
            pub = cert.public_key()
            key_size = getattr(pub, "key_size", None)
            key_algorithm = "RSA" if isinstance(pub, rsa.RSAPublicKey) else "EC" if isinstance(pub, ec.EllipticCurvePublicKey) else "DSA" if isinstance(pub, dsa.DSAPublicKey) else type(pub).__name__
            signature = cert.signature_hash_algorithm.name.upper() if cert.signature_hash_algorithm else "UNKNOWN"
            now = datetime.now(timezone.utc)
            valid_until = cert.not_valid_after_utc
            valid_from = cert.not_valid_before_utc
            days = (valid_until - now).total_seconds() / 86400
            tls = conn.version() or "UNKNOWN"
            cipher = (conn.cipher() or ("UNKNOWN",))[0]
            hostname_match = False
            try:
                ssl.match_hostname({"subject": (("commonName", cn),), "subjectAltName": [("DNS", x) for x in san]}, hostname)
                hostname_match = True
            except Exception:
                pass
            findings = []
            if days < 0: findings.append("Expired certificate")
            elif days <= 30: findings.append("Certificate expires within 30 days")
            if subject == issuer: findings.append("Self-signed certificate")
            if key_algorithm == "RSA" and key_size and key_size < 2048: findings.append("Weak RSA key")
            if any(x in signature for x in ("SHA1", "MD5")): findings.append("Weak signature algorithm")
            if tls in ("TLSv1", "TLSv1.1"): findings.append(f"Weak TLS version enabled: {tls}")
            if not hostname_match: findings.append("Invalid hostname")
            try:
                conn.settimeout(3)
                conn.sendall(f"HEAD / HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n".encode())
                headers = conn.recv(8192).decode("iso-8859-1", "ignore").lower()
                hsts = "strict-transport-security:" in headers
            except Exception:
                hsts = False
            if not hsts: findings.append("Missing HSTS")
            risk = "high" if any("Expired" in x or "Weak" in x or "Invalid" in x for x in findings) else "medium" if findings else "low"
            grade = "A" if not findings and tls in ("TLSv1.2", "TLSv1.3") and hsts else "A-" if tls in ("TLSv1.2", "TLSv1.3") and len(findings) <= 1 else "B" if len(findings) <= 2 else "C" if len(findings) <= 4 else "D" if len(findings) <= 6 else "F"
            return {"issuer": issuer, "subject": subject, "common_name": cn, "san": san, "tls_version": tls, "cipher": cipher, "signature_algorithm": signature, "public_key_algorithm": key_algorithm, "key_size": key_size, "certificate_version": cert.version.name, "valid_from": valid_from, "valid_until": valid_until, "days_remaining": max(0, int(days)), "expired": days < 0, "self_signed": subject == issuer, "hostname_match": hostname_match, "hsts_enabled": hsts, "risk_level": risk, "findings": findings, "certificate_chain_length": 1, "ssl_grade": grade}


class SSLAnalysisExecutor(BaseStageExecutor):
    def __init__(self): super().__init__(stage=ScanStage.SSL_ANALYSIS, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db) -> dict:
        try:
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan: return self._error("Scan record not found for SSL Analysis")
            project_id = str(scan.get("project_id", "")); assets = await db.assets.find({"project_id": project_id, "scan_id": scan_id, "is_live": True, "https_enabled": True}).to_list(None)
            await self._logs(db, scan_id, [log_event("SSL Analysis started"), log_event(f"Analyzing {len(assets)} live HTTPS assets")])
            saved = 0
            for asset in assets:
                hostname = asset.get("hostname", "")
                try:
                    await self._log(db, scan_id, f"Analyzing {hostname}")
                    result = await asyncio.wait_for(asyncio.to_thread(_analyse, hostname, asset.get("ip")), timeout=15)
                    now = datetime.utcnow(); key = {"project_id": project_id, "asset_id": str(asset["_id"])}
                    await db.ssl_analysis.update_one(key, {"$setOnInsert": {"first_seen": now, "created_at": now}, "$set": {**result, "scan_id": scan_id, "hostname": hostname, "ip": asset.get("ip"), "last_seen": now, "updated_at": now}}, upsert=True)
                    await db.assets.update_one({"_id": asset["_id"]}, {"$set": {"ssl_enabled": True, "certificate_expiry": result["valid_until"], "days_remaining": result["days_remaining"], "tls_version": result["tls_version"], "cipher": result["cipher"], "ssl_grade": result["ssl_grade"], "ssl_last_scan": now, "updated_at": now}})
                    for finding in result["findings"]: await self._log(db, scan_id, f"{hostname}: {finding}", "warning")
                    await self._log(db, scan_id, f"{hostname}: SSL Grade: {result['ssl_grade']}"); saved += 1
                except Exception as exc:
                    await self._log(db, scan_id, f"SSL analysis failed for {hostname}: {type(exc).__name__}", "warning")
                    await db.assets.update_one({"_id": asset["_id"]}, {"$set": {"ssl_enabled": False, "ssl_last_scan": datetime.utcnow()}})
            await self._log(db, scan_id, "SSL Analysis completed")
            return {"status": "success", "stage": self.stage.value, "message": f"Saved SSL analysis for {saved} assets", "data": {"analyzed": saved}}
        except Exception as exc:
            logger.exception("SSL analysis failed")
            return self._error(f"SSL Analysis failed: {type(exc).__name__}: {exc}")

    async def _log(self, db, scan_id, message, level="info"): await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": log_event(message, level)}})
    async def _logs(self, db, scan_id, entries): await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$push": {"logs": {"$each": entries}}})
    def _error(self, message): return {"status": "error", "stage": self.stage.value, "message": message}
