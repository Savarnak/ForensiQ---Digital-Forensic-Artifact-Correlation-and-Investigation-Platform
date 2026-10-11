import pytest
from app.orchestrator.state import CaseState
from app.orchestrator.brain_graph import investigation_graph
from app.tools.registry import tool_registry

@pytest.mark.asyncio
async def test_langgraph_planner_node_pipeline_integration():
    initial_state = CaseState(
        case_id="CASE-INTEG-100",
        case_number="CASE-INTEG-NUM",
        investigation_goal="Identify relevant relationships between accounts, devices, locations and events",
        evidence_items=[
            {"id": "EV-1", "file_name": "chats.json", "file_type": "CHAT_LOG"},
            {"id": "EV-2", "file_name": "evidence_photo_01.jpg", "file_type": "IMAGE"}
        ]
    )

    state_input_dict = initial_state.model_dump() if hasattr(initial_state, "model_dump") else initial_state.dict()
    final_state_dict = await investigation_graph.ainvoke(state_input_dict)

    assert final_state_dict["case_id"] == "CASE-INTEG-100"
    assert len(final_state_dict["tasks"]) >= 2
    assert len(final_state_dict["audit_events"]) >= 4

    event_types = [ae["event_type"] for ae in final_state_dict["audit_events"]]
    assert "GOAL_UNDERSTOOD" in event_types
    assert "EVIDENCE_INSPECTED" in event_types
    assert "TASKS_PLANNED" in event_types
    assert "FINDINGS_EVALUATED" in event_types
