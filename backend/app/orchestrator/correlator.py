from app.orchestrator.state import CaseState
from app.correlation.fusion_service import IntelligenceFusionService
from app.core.logging import logger

async def correlator_node(state: CaseState) -> CaseState:
    """Correlates findings across evidence sources using IntelligenceFusionService."""
    logger.info(f"[Correlator Node] Executing Intelligence Fusion for Case ID: {state.case_id}")
    return await IntelligenceFusionService.correlate_state_findings(state)
