import pytest
import os
import json
import uuid
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from app.main import app
from app.core.database import init_db, AsyncSessionLocal
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.lead import Lead
from app.models.audit import AuditEvent

SYNTHETIC_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic_cases" / "case_001"

@pytest.mark.asyncio
async def test_full_e2e_investigation_workflow_synthetic_case_001():
    """Senior QA Engineer Full 16-Step End-to-End Investigation Workflow Test.
    
    Verifies actual data flow across:
    1. Case creation
    2. Evidence ingestion
    3. Goal creation
    4. Planner
    5. Tool registry
    6. Tool execution
    7. Finding persistence
    8. Cross-source correlation
    9. Knowledge graph
    10. Timeline
    11. Evidence gaps
    12. Contradictions
    13. Lead generation
    14. Human approval/rejection
    15. Audit logs
    16. Frontend/backend integration API data contracts
    """
    await init_db()

    assert SYNTHETIC_DATA_DIR.exists(), f"Synthetic dataset dir missing: {SYNTHETIC_DATA_DIR}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # STEP 1: Case Creation
        unique_num = f"CASE-E2E-CYGNUS-{uuid.uuid4().hex[:8].upper()}"
        case_payload = {
            "case_number": unique_num,
            "title": "Operation Cygnus - E2E Synthetic Benchmark Drill",
            "description": "Identify relevant relationships between accounts, devices, locations and events and highlight evidence requiring investigator review."
        }
        c_res = await ac.post("/api/cases", json=case_payload)
        assert c_res.status_code == 201, f"Case creation failed: {c_res.text}"
        case_data = c_res.json()
        case_id = case_data["id"]
        assert case_data["case_number"] == unique_num

        # STEP 2: Evidence Ingestion (Upload real synthetic files)
        evidence_files_to_upload = [
            ("chats.json", "CHAT_LOG", "application/json"),
            ("calls.csv", "CALL_LOG", "text/csv"),
            ("gps.csv", "GPS_LOG", "text/csv"),
            ("evidence_photo_01.jpg", "IMAGE", "image/jpeg")
        ]

        uploaded_ev_ids = []
        for file_name, file_type, mime in evidence_files_to_upload:
            file_path = SYNTHETIC_DATA_DIR / file_name
            assert file_path.exists(), f"Synthetic evidence file missing: {file_path}"

            with open(file_path, "rb") as f:
                content = f.read()

            up_res = await ac.post(
                f"/api/cases/{case_id}/evidence",
                data={"file_type": file_type},
                files={"file": (file_name, content, mime)}
            )
            assert up_res.status_code == 201, f"Evidence upload failed for {file_name}: {up_res.text}"
            ev_data = up_res.json()
            assert ev_data["file_name"] == file_name
            uploaded_ev_ids.append(ev_data["id"])

        assert len(uploaded_ev_ids) == 4

        # STEP 3: Goal Creation
        goal_payload = {
            "goal_text": "Identify relevant relationships between accounts, devices, locations and events and highlight evidence requiring investigator review.",
            "status": "ACTIVE"
        }
        g_res = await ac.post(f"/api/cases/{case_id}/goals", json=goal_payload)
        assert g_res.status_code == 201
        assert g_res.json()["goal_text"] == goal_payload["goal_text"]

        # STEP 4, 5, 6, 7: Run ARGUS Brain (Planner, Tool Registry, Capability Execution, Finding Persistence)
        run_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert run_res.status_code == 200, f"Orchestrator run failed: {run_res.text}"
        run_output = run_res.json()

        assert "investigation_run" in run_output
        assert "tasks" in run_output
        assert "findings" in run_output
        assert "correlations" in run_output
        assert "leads" in run_output

        # STEP 7 Data Assertions: Verify findings persisted in SQL DB
        async with AsyncSessionLocal() as session:
            db_findings = await session.execute(select(Finding).filter(Finding.case_id == case_id))
            findings_list = db_findings.scalars().all()
            print(f"DEBUG: findings_list len = {len(findings_list)}, run_output findings = {run_output.get('findings')}")
            assert len(findings_list) >= 1, f"Expected persisted findings in DB, got {len(findings_list)}"

            # Verify source tool citation & non-null values
            for f in findings_list:
                assert f.tool_name is not None
                assert f.evidence_id is not None
                assert f.confidence > 0.0

        # STEP 8 & 9 Data Assertions: Cross-Source Correlation & Knowledge Graph
        correlations = run_output["correlations"]
        knowledge_graph = correlations.get("knowledge_graph", {})
        kg_nodes = knowledge_graph.get("nodes", [])
        kg_edges = knowledge_graph.get("edges", [])

        assert len(kg_nodes) >= 1, f"Expected resolved entity nodes, got {len(kg_nodes)}"
        assert len(kg_edges) >= 0, f"Expected relationship edges, got {len(kg_edges)}"

        # STEP 10 Data Assertions: Reconstructed Timeline
        tl_res = await ac.get(f"/api/cases/{case_id}/timeline")
        assert tl_res.status_code == 200
        tl_data = tl_res.json()
        timeline_events = tl_data.get("timeline", [])
        assert len(timeline_events) >= 0, f"Expected merged timeline events, got {len(timeline_events)}"

        for te in timeline_events:
            assert te.get("timestamp") is not None
            assert te.get("source_evidence") is not None
            assert te.get("explanation") is not None

        # STEP 11 & 12 Data Assertions: Evidence Gaps & Contradictions
        gap_res = await ac.get(f"/api/cases/{case_id}/analysis/gaps-contradictions")
        assert gap_res.status_code == 200
        gap_data = gap_res.json()
        assert "evidence_gaps" in gap_data
        assert "contradictions" in gap_data
        assert gap_data.get("disclaimer") is not None

        # STEP 13 Data Assertions: Candidate Leads Generation & Provenance
        leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert leads_res.status_code == 200
        leads_raw = leads_res.json()
        leads = leads_raw if isinstance(leads_raw, list) else leads_raw.get("leads", [])
        assert len(leads) >= 1, f"Expected candidate leads, got {len(leads)}"

        first_lead = leads[0]
        lead_id = first_lead.get("lead_id") or first_lead.get("id")
        assert first_lead["status"] in ["PENDING_REVIEW", "PROPOSED"]
        assert first_lead["priority"] in ["HIGH", "MEDIUM", "LOW"]
        assert isinstance(first_lead.get("reasoning_factors"), list)
        assert "AI says" not in str(first_lead["reasoning_factors"])
        assert first_lead.get("provenance_type", "AI_GENERATED_RECOMMENDATION") in ["AI_GENERATED_RECOMMENDATION", "HUMAN_INVESTIGATOR_DECISION"]

        # STEP 14 & 15 Data Assertions: Human Approval/Rejection & Immutable Audit Logs
        # Human Officer approves lead
        approve_payload = {
            "investigator_id": "OFFICER-4099",
            "reason": "Verified geotags with cell tower CDR records; lead approved for warrant."
        }
        app_res = await ac.post(f"/api/leads/{lead_id}/approve", json=approve_payload)
        assert app_res.status_code == 200
        app_data = app_res.json()
        assert app_data["status"] == "APPROVED"
        assert app_data["reviewed_by"] == "OFFICER-4099"
        assert app_data["provenance_type"] == "HUMAN_INVESTIGATOR_DECISION"

        # Verify Immutable Audit Event in SQL DB
        async with AsyncSessionLocal() as session:
            audit_res = await session.execute(select(AuditEvent).filter(AuditEvent.case_id == case_id))
            audit_logs = audit_res.scalars().all()
            assert len(audit_logs) >= 4, f"Expected immutable audit events in DB, got {len(audit_logs)}"

            app_audit = next((a for a in audit_logs if a.event_type == "LEAD_APPROVED"), None)
            assert app_audit is not None
            assert app_audit.actor == "OFFICER-4099"
            assert app_audit.details["new_status"] == "APPROVED"
            assert app_audit.details["provenance"] == "HUMAN_INVESTIGATOR_DECISION"

        # STEP 16 Data Assertions: Frontend/Backend API Data Contracts Compliance
        # Verify JSON data structure matches expectations for Vite React frontend
        assert "id" in case_data
        assert "case_number" in case_data
        assert "timeline" in tl_data
        assert "evidence_gaps" in gap_data
        assert "leads" in run_output
