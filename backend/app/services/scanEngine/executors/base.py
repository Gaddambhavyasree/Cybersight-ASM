import asyncio
import logging
from abc import ABC, abstractmethod
from app.models.scan import ScanStage

logger = logging.getLogger(__name__)


class BaseStageExecutor(ABC):
    def __init__(self, stage: ScanStage, simulated_delay: float = 1.0):
        self.stage = stage
        self.simulated_delay = simulated_delay

    @abstractmethod
    async def execute(self, scan_id: str, target: str, db) -> dict:
        pass

    async def simulate(self, scan_id: str, target: str, db) -> dict:
        logger.info(f"[{scan_id}] Simulating {self.stage.value} for target={target}")
        await asyncio.sleep(self.simulated_delay)
        return {
            "status": "success",
            "stage": self.stage.value,
            "message": f"{self.stage.value} completed (simulated)",
            "data": {},
        }
