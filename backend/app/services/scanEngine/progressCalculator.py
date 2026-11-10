from app.models.scan import ScanStage
from app.services.scanEngine.workflow import STAGE_PROGRESS


def calculate_progress(current_stage: ScanStage) -> int:
    return STAGE_PROGRESS.get(current_stage, 0)


def calculate_stage_progress(current_stage: ScanStage, total_stages: int = 12) -> float:
    stage_progress = STAGE_PROGRESS.get(current_stage, 0)
    return stage_progress / 100.0
