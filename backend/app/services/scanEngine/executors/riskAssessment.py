import logging
from datetime import datetime
from bson import ObjectId
from app.models.scan import ScanStage
from app.services.scanEngine.executors.base import BaseStageExecutor
from app.services.scanEngine.logger import log_event

logger = logging.getLogger(__name__)
HIGH_PORTS = {21, 22, 23, 25, 110, 143, 445, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 9200, 27017}
MEDIUM_PORTS = {8080, 8443, 8888}
LEVELS = ("Critical", "High", "Medium", "Low", "Very Low")


def risk_level(score: int) -> str:
    return "Very Low" if score <= 20 else "Low" if score <= 40 else "Medium" if score <= 60 else "High" if score <= 80 else "Critical"


def _num(value, default=0):
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return float(default)


class RiskAssessmentExecutor(BaseStageExecutor):
    def __init__(self):
        super().__init__(stage=ScanStage.RISK_ASSESSMENT, simulated_delay=0)

    async def execute(self, scan_id: str, target: str, db):
        scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            return self._error("Scan record not found for Risk Assessment")
        project_id = str(scan.get("project_id", ""))
        assets = await db.assets.find({"project_id": project_id}).to_list(None)
        await self._logs(db, scan_id, [log_event("Risk Assessment started"), log_event(f"Calculating risk for {len(assets)} assets")])
        results = []
        for asset in assets:
            try:
                result = await self._calculate(asset, project_id, db)
                now = datetime.utcnow()
                await db.assets.update_one({"_id": asset["_id"]}, {"$set": {**result, "last_risk_calculation": now, "updated_at": now}})
                results.append({"asset_id": str(asset["_id"]), "hostname": asset.get("hostname"), "score": result["risk_score"], "level": result["risk_level"]})
                await self._log(db, scan_id, f"{asset.get('hostname', 'unknown')} Risk Score {result['risk_score']} ({result['risk_level']})")
            except Exception:
                logger.exception("Risk calculation failed for asset %s", asset.get("_id"))
        average = round(sum(x["score"] for x in results) / len(results)) if results else 0
        highest = max(results, key=lambda x: x["score"], default=None)
        distribution = {level: sum(x["level"] == level for x in results) for level in LEVELS}
        project_update = {"risk_score": average, "risk_level": risk_level(average), "average_asset_risk": average,
                          "highest_asset_risk": highest["score"] if highest else 0, "critical_assets": distribution["Critical"],
                          "high_assets": distribution["High"], "medium_assets": distribution["Medium"], "low_assets": distribution["Low"],
                          "risk_distribution": distribution, "last_risk_calculation": datetime.utcnow()}
        try:
            await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": project_update})
        except Exception:
            logger.exception("Could not update project risk summary")
        await self._logs(db, scan_id, [log_event(f"Project Risk Score {average} ({risk_level(average)})"), log_event("Risk Assessment completed")])
        return {"status": "success", "stage": self.stage.value, "message": f"Calculated risk for {len(results)} assets", "data": {"assets": len(results), "score": average}}

    async def _calculate(self, asset, project_id, db):
        aid = str(asset["_id"])
        ports = await db.ports.find({"project_id": project_id, "asset_id": aid, "state": "open"}).to_list(None)
        vulns = await db.vulnerabilities.find({"project_id": project_id, "asset_id": aid}).to_list(None)
        ssl = await db.ssl_analysis.find_one({"project_id": project_id, "asset_id": aid}) or {}
        tech = await db.technologies.find({"project_id": project_id, "asset_id": aid}).to_list(None)
        intel = await db.threat_intelligence.find({"project_id": project_id, "asset_id": aid}).to_list(None)
        exposure = (10 if asset.get("is_live") and asset.get("https_enabled") else 0) + (10 if asset.get("is_live") and not asset.get("https_enabled") else 0)
        exposure += min(5, _num(asset.get("admin_panels"))) + min(5, _num(asset.get("api_count") or asset.get("endpoint_count")))
        port_score = min(20, sum(3 if _num(p.get("port")) in HIGH_PORTS else 1 if _num(p.get("port")) in MEDIUM_PORTS else .25 for p in ports))
        vuln_score = min(35, sum({"critical": 12, "high": 8, "medium": 4, "low": 1}.get(str(v.get("severity", "low")).lower(), 0) for v in vulns) + sum(8 for v in vulns if v.get("kev")))
        ssl_score = min(15, (5 if ssl.get("expired") else 0) + (3 if ssl.get("self_signed") else 0) + (3 if ssl.get("tls_version") in ("TLSv1", "TLSv1.1") else 0) + (2 if not ssl.get("hsts_enabled") else 0) + (2 if not ssl.get("hostname_match", True) else 0))
        risky_names = ("apache", "php", "wordpress", "drupal", "joomla", "iis", "plesk", "asp.net", "jquery", "bootstrap", "modernizr")
        tech_score = min(10, sum(2 for t in tech if any(n in str(t.get("technology_name", "")).lower() for n in risky_names)))
        ti_score = min(10, sum(5 for t in intel if t.get("kev") or t.get("shodan") or t.get("public_exploit") or _num(t.get("virustotal", {}).get("malicious"))))
        breakdown = {"internet_exposure": round(exposure), "ports": round(port_score), "vulnerabilities": round(vuln_score), "ssl": round(ssl_score), "technologies": round(tech_score), "threat_intelligence": round(ti_score)}
        score = min(100, sum(breakdown.values()))
        recommendations = [f"Review or close high-risk port {p.get('port')}" for p in ports if _num(p.get("port")) in HIGH_PORTS]
        if ssl.get("expired"): recommendations.append("Renew SSL certificate")
        if ssl.get("self_signed"): recommendations.append("Replace self-signed certificate")
        if not ssl.get("hsts_enabled") and ssl: recommendations.append("Enable HSTS")
        recommendations += [f"Patch {v.get('cve') or v.get('template_name', 'high severity finding')}" for v in vulns if str(v.get("severity", "")).lower() in ("critical", "high")]
        return {"risk_score": score, "risk_level": risk_level(score), "risk_factors": list(breakdown), "risk_breakdown": breakdown, "risk_recommendations": list(dict.fromkeys(recommendations))}

    async def _log(self, db, sid, message, level="info"):
        await db.scans.update_one({"_id": ObjectId(sid)}, {"$push": {"logs": log_event(message, level)}})

    async def _logs(self, db, sid, entries):
        await db.scans.update_one({"_id": ObjectId(sid)}, {"$push": {"logs": {"$each": entries}}})

    def _error(self, message):
        return {"status": "error", "stage": self.stage.value, "message": message}
