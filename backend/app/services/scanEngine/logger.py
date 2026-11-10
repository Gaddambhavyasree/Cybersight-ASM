from datetime import datetime
from app.models.scan import ScanLog, ScanStage
from app.services.scanEngine.workflow import STAGE_LABELS


def log_event(message: str, level: str = "info") -> dict:
    return ScanLog(
        message=message,
        timestamp=datetime.utcnow(),
        level=level,
    ).model_dump()


def log_scan_started(scan_id: str) -> dict:
    return log_event(f"Scan {scan_id} started", "info")


def log_workflow_initialized() -> dict:
    return log_event("Workflow initialized", "info")


def log_entering_stage(stage: ScanStage) -> dict:
    label = STAGE_LABELS.get(stage, stage.value)
    return log_event(f"Entering {label}", "info")


def log_stage_completed(stage: ScanStage) -> dict:
    label = STAGE_LABELS.get(stage, stage.value)
    return log_event(f"{label} completed", "info")


def log_stage_failed(stage: ScanStage, error: str) -> dict:
    label = STAGE_LABELS.get(stage, stage.value)
    return log_event(f"{label} failed: {error}", "error")


def log_workflow_completed() -> dict:
    return log_event("Workflow completed successfully", "info")


def log_workflow_failed(failed_stage: ScanStage, error: str) -> dict:
    label = STAGE_LABELS.get(failed_stage, failed_stage.value)
    return log_event(f"Workflow failed at {label}: {error}", "error")


def log_scan_cancelled() -> dict:
    return log_event("Scan cancelled by user", "warning")
