from app.models.scan import ScanStage


WORKFLOW_STAGES = [
    ScanStage.WAITING,
    ScanStage.ASSET_DISCOVERY,
    ScanStage.LIVE_HOST_DETECTION,
    ScanStage.PORT_SCANNING,
    ScanStage.TECHNOLOGY_DETECTION,
    ScanStage.DNS_INTELLIGENCE,
    ScanStage.SSL_ANALYSIS,
    ScanStage.WEB_CRAWLING,
    ScanStage.VULNERABILITY_ASSESSMENT,
    ScanStage.THREAT_INTELLIGENCE,
    ScanStage.RISK_ASSESSMENT,
    ScanStage.COMPLETED,
]

STAGE_PROGRESS = {
    ScanStage.WAITING: 0,
    ScanStage.ASSET_DISCOVERY: 10,
    ScanStage.LIVE_HOST_DETECTION: 20,
    ScanStage.PORT_SCANNING: 30,
    ScanStage.TECHNOLOGY_DETECTION: 40,
    ScanStage.DNS_INTELLIGENCE: 50,
    ScanStage.SSL_ANALYSIS: 60,
    ScanStage.WEB_CRAWLING: 70,
    ScanStage.VULNERABILITY_ASSESSMENT: 80,
    ScanStage.THREAT_INTELLIGENCE: 90,
    ScanStage.RISK_ASSESSMENT: 95,
    ScanStage.COMPLETED: 100,
}

STAGE_LABELS = {
    ScanStage.WAITING: "Waiting",
    ScanStage.ASSET_DISCOVERY: "Asset Discovery",
    ScanStage.LIVE_HOST_DETECTION: "Live Host Verification",
    ScanStage.PORT_SCANNING: "Port Discovery",
    ScanStage.TECHNOLOGY_DETECTION: "Technology Detection",
    ScanStage.DNS_INTELLIGENCE: "DNS Intelligence",
    ScanStage.SSL_ANALYSIS: "SSL Analysis",
    ScanStage.WEB_CRAWLING: "Web Crawling",
    ScanStage.VULNERABILITY_ASSESSMENT: "Vulnerability Assessment",
    ScanStage.THREAT_INTELLIGENCE: "Threat Intelligence",
    ScanStage.RISK_ASSESSMENT: "Risk Assessment",
    ScanStage.COMPLETED: "Completed",
}


def get_next_stage(current_stage: ScanStage) -> ScanStage | None:
    try:
        idx = WORKFLOW_STAGES.index(current_stage)
        if idx + 1 < len(WORKFLOW_STAGES):
            return WORKFLOW_STAGES[idx + 1]
    except ValueError:
        pass
    return None


def get_stage_index(stage: ScanStage) -> int:
    try:
        return WORKFLOW_STAGES.index(stage)
    except ValueError:
        return -1


def is_terminal_stage(stage: ScanStage) -> bool:
    return stage in (ScanStage.COMPLETED,)
