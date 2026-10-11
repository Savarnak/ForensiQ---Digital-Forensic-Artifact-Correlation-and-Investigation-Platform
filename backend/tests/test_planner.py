import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.orchestrator.state import CaseState
from app.orchestrator.brain_graph import investigation_graph
from app.tools.registry import tool_registry

INVESTIGATION_GOAL_INPUT = (
    "Identify relevant relationships between accounts, devices, locations and events "
    "and highlight evidence requiring investigator review."
)

@pytest.mark.asyncio
async def test_agentic_planner_state_graph_workflow():
    """Tests the full LangGraph state machine execution loop."""
    initial_state = CaseState(
        case_id="CASE-PLANNER-TEST-001",
        case_number="CASE-2026-PLANNER",
        investigation_goal=INVESTIGATION_GOAL_INPUT,
        evidence_items=[
            {
                "id": "EVID-001",
                "file_name": "suspect_chat_log.txt",
                "file_path": "./data/synthetic/suspect_chat_log.txt",
                "file_type": "CHAT_LOG",
                "text_content": "@CyberHawk communicated with @NightOwl on 2026-08-10T14:00:00Z."
            },
            {
                "id": "EVID-002",
                "file_name": "surveillance_photo.jpg",
                "file_path": "./data/synthetic/surveillance_photo.jpg",
                "file_type": "IMAGE",
                "extracted_metadata": {
                    "synthetic_exif": {
                        "gps_coordinates": {"latitude": 37.7749, "longitude": -122.4194},
                        "device_model": "Samsung Galaxy S22"
                    },
                    "synthetic_ocr_text": "CONFIDENTIAL NOTICE: Meet @NightOwl at coordinates 37.7749,-122.4194"
                }
            }
        ]
    )

    state_input_dict = initial_state.model_dump() if hasattr(initial_state, "model_dump") else initial_state.dict()
    final_state = await investigation_graph.ainvoke(state_input_dict)

    # 1. Verify Goal Understanding & Evidence Inspection
    assert len(final_state["execution_logs"]) >= 5
    assert any("Goal Analyzed" in log for log in final_state["execution_logs"])
    assert any("Evidence Inspected" in log for log in final_state["execution_logs"])

    # 2. Verify Task Planning and Tool Matching
    tasks = final_state["tasks"]
    assert len(tasks) >= 3
    tool_names_used = [t["tool_name"] for t in tasks]
    # Enforce tool execution strictly through registered tool interface
    for name in tool_names_used:
        assert tool_registry.get(name) is not None

    # 3. Verify Findings Storage
    raw_findings = final_state["raw_findings"]
    std_findings = final_state["standardized_findings"]
    assert len(raw_findings) >= 1
    assert len(std_findings) >= 1

    # 4. Verify Iterative Evaluation Loop
    assert final_state["iteration_count"] >= 1

    # 5. Verify Correlation (Knowledge Graph & Timeline)
    nodes = final_state["knowledge_graph_nodes"]
    edges = final_state["knowledge_graph_edges"]
    timeline = final_state["timeline_events"]
    assert len(nodes) >= 1

    # 6. Verify Candidates Leads & Human Review Flag
    proposed_leads = final_state["proposed_leads"]
    assert len(proposed_leads) >= 1
    for lead in proposed_leads:
        assert lead["status"] == "PROPOSED"
        assert len(lead["supporting_evidence_ids"]) >= 1

    # 7. Verify Audit Event Logging
    audit_events = final_state["audit_events"]
    assert len(audit_events) >= 3
    event_types = [ae["event_type"] for ae in audit_events]
    assert "GOAL_UNDERSTOOD" in event_types
    assert "EVIDENCE_INSPECTED" in event_types
    assert "FINDINGS_EVALUATED" in event_types
    assert "HUMAN_REVIEW_FLAGGED" in event_types

@pytest.mark.asyncio
async def test_orchestrator_api_endpoint():
    """End-to-end test of /api/orchestrator/run/{case_id} REST API."""
    await init_db()
    unique_num = f"CASE-2026-BRAIN-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Case
        case_res = await ac.post("/api/cases", json={
            "case_number": unique_num,
            "title": "Operation Cygnus - Agentic Planner Test",
            "description": INVESTIGATION_GOAL_INPUT
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # Add Evidence
        files = {"file": ("chat_evidence.txt", b"@CyberHawk meeting with @NightOwl at +1-555-0199.", "text/plain")}
        data = {"file_type": "CHAT_LOG"}
        ev_res = await ac.post(f"/api/cases/{case_id}/evidence", data=data, files=files)
        assert ev_res.status_code == 201

        # Run Brain Orchestration Endpoint
        orch_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert orch_res.status_code == 200
        res_data = orch_res.json()

        assert res_data["status"] == "success"
        assert "investigation_run" in res_data
        assert res_data["investigation_run"]["status"] == "COMPLETED"
        assert "tasks" in res_data
        assert "findings" in res_data
        assert "correlations" in res_data
        assert "leads" in res_data
        assert "audit_events" in res_data
        assert len(res_data["leads"]) >= 1
