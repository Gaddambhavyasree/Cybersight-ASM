import asyncio
import logging
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.models.scan import ScanStage, ScanStatus
from app.services.scanEngine.workflow import (
    WORKFLOW_STAGES, get_next_stage, is_terminal_stage,
)
from app.services.scanEngine.stageManager import StageManager
from app.services.scanEngine.progressCalculator import calculate_progress
from app.services.scanEngine.logger import (
    log_scan_started, log_workflow_initialized, log_workflow_failed, log_event,
)
from app.services.scanEngine.executors.assetDiscovery import AssetDiscoveryExecutor
from app.services.scanEngine.executors.liveHostVerification import LiveHostVerificationExecutor
from app.services.scanEngine.executors.portDiscovery import PortDiscoveryExecutor
from app.services.scanEngine.executors.technologyDetection import TechnologyDetectionExecutor
from app.services.scanEngine.executors.dnsIntelligence import DNSIntelligenceExecutor
from app.services.scanEngine.executors.sslAnalysis import SSLAnalysisExecutor
from app.services.scanEngine.executors.webCrawling import WebCrawlingExecutor
from app.services.scanEngine.executors.vulnerabilityAssessment import VulnerabilityAssessmentExecutor
from app.services.scanEngine.executors.threatIntelligence import ThreatIntelligenceExecutor
from app.services.scanEngine.executors.riskAssessment import RiskAssessmentExecutor

logger = logging.getLogger(__name__)

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


class ScanEngine:
    def __init__(self):
        self._active_scans: dict[str, asyncio.Task] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._executors = {
            ScanStage.ASSET_DISCOVERY: AssetDiscoveryExecutor(),
            ScanStage.LIVE_HOST_DETECTION: LiveHostVerificationExecutor(),
            ScanStage.PORT_SCANNING: PortDiscoveryExecutor(),
            ScanStage.TECHNOLOGY_DETECTION: TechnologyDetectionExecutor(),
            ScanStage.DNS_INTELLIGENCE: DNSIntelligenceExecutor(),
            ScanStage.SSL_ANALYSIS: SSLAnalysisExecutor(),
            ScanStage.WEB_CRAWLING: WebCrawlingExecutor(),
            ScanStage.VULNERABILITY_ASSESSMENT: VulnerabilityAssessmentExecutor(),
            ScanStage.THREAT_INTELLIGENCE: ThreatIntelligenceExecutor(),
            ScanStage.RISK_ASSESSMENT: RiskAssessmentExecutor(),
        }

    async def start(self, scan_id: str, db: AsyncIOMotorDatabase) -> None:
        cancel_event = asyncio.Event()
        self._cancel_events[scan_id] = cancel_event

        task = asyncio.create_task(self._run_workflow(scan_id, db, cancel_event))
        self._active_scans[scan_id] = task
        task.add_done_callback(lambda _: self._cleanup(scan_id))

    def _cleanup(self, scan_id: str) -> None:
        self._active_scans.pop(scan_id, None)
        self._cancel_events.pop(scan_id, None)

    def is_running(self, scan_id: str) -> bool:
        return scan_id in self._active_scans

    async def cancel(self, scan_id: str) -> bool:
        event = self._cancel_events.get(scan_id)
        if event:
            event.set()
            return True
        return False

    async def _run_workflow(
        self, scan_id: str, db: AsyncIOMotorDatabase, cancel_event: asyncio.Event,
    ) -> None:
        stage_mgr = StageManager(db)

        try:
            scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return

            project = await db.projects.find_one({"_id": ObjectId(scan["project_id"])})
            if not project:
                error_msg = f"Project {scan['project_id']} not found"
                await stage_mgr.mark_stage_failed(scan_id, ScanStage.WAITING, error_msg)
                logger.error(f"Scan {scan_id} failed: {error_msg}")
                return

            target_domain = project.get("target_domain", "").strip()

            if not target_domain:
                error_msg = "Project has no target domain configured"
                await stage_mgr.mark_stage_failed(scan_id, ScanStage.WAITING, error_msg)
                logger.error(f"Scan {scan_id} failed: {error_msg}")
                return

            if not DOMAIN_REGEX.match(target_domain):
                error_msg = f"Invalid target domain: {target_domain}"
                await stage_mgr.mark_stage_failed(scan_id, ScanStage.WAITING, error_msg)
                logger.error(f"Scan {scan_id} failed: {error_msg}")
                return

            await db.scans.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": {"target_domain": target_domain}},
            )

            logger.info(f"Scan {scan_id} targeting domain: {target_domain}")

            now = datetime.utcnow()
            init_logs = [log_scan_started(scan_id), log_workflow_initialized()]
            await db.scans.update_one(
                {"_id": ObjectId(scan_id)},
                {
                    "$set": {
                        "status": ScanStatus.RUNNING.value,
                        "started_at": now,
                        "updated_at": now,
                    },
                    "$push": {"logs": {"$each": init_logs}},
                },
            )

            current_stage = ScanStage.WAITING

            while current_stage is not None:
                if cancel_event.is_set():
                    await stage_mgr.mark_scan_cancelled(scan_id)
                    logger.info(f"Scan {scan_id} cancelled")
                    return

                if is_terminal_stage(current_stage):
                    await stage_mgr.mark_scan_completed(scan_id)
                    logger.info(f"Scan {scan_id} completed")
                    return

                await stage_mgr.transition_to(scan_id, current_stage)

                executor = self._executors.get(current_stage)
                if executor:
                    try:
                        result = await executor.execute(scan_id, target_domain, db)

                        if cancel_event.is_set():
                            await stage_mgr.mark_scan_cancelled(scan_id)
                            logger.info(f"Scan {scan_id} cancelled during {current_stage.value}")
                            return

                        if result.get("status") == "success":
                            await stage_mgr.mark_stage_completed(scan_id, current_stage)
                        else:
                            error_msg = result.get("message", "Stage execution failed")
                            await stage_mgr.mark_stage_failed(scan_id, current_stage, error_msg)
                            logger.error(f"Scan {scan_id} failed at {current_stage.value}: {error_msg}")
                            return
                    except Exception as e:
                        error_msg = str(e)
                        await stage_mgr.mark_stage_failed(scan_id, current_stage, error_msg)
                        logger.error(f"Scan {scan_id} exception at {current_stage.value}: {error_msg}")
                        return

                current_stage = get_next_stage(current_stage)

        except asyncio.CancelledError:
            await stage_mgr.mark_scan_cancelled(scan_id)
            logger.info(f"Scan {scan_id} task cancelled")
        except Exception as e:
            try:
                await stage_mgr.mark_stage_failed(
                    scan_id, ScanStage.WAITING, str(e)
                )
            except Exception:
                logger.error(f"Scan {scan_id} critical failure: {e}")
