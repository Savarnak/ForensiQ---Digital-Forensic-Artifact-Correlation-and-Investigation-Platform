import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from app.main import app
from app.core.database import init_db, AsyncSessionLocal
from app.models.lead import Lead, LeadStatus
from app.models.audit import AuditEvent
from app.models.case import Case

@pytest.mark.asyncio
async def test_human_review_lead_lifecycle_and_audit_events():
    await init_db()
    case_num = f"CASE-HUMAN-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Case
        c_res = await ac.post("/api/cases", json={"case_number": case_num, "title": "Human Review Test Case"})
        assert c_res.status_code == 201
        case_id = c_res.json()["id"]

        # 2. Add Evidence & Run Orchestration to generate candidate lead
        ev_res = await ac.post(f"/api/cases/{case_id}/evidence", data={"file_type": "CHAT_LOG"}, files={"file": ("chat.txt", b"@CyberHawk meeting with @NightOwl.", "text/plain")})
        assert ev_res.status_code == 201

        # Run Brain Orchestration Endpoint
        orch_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert orch_res.status_code == 200

        # Fetch candidate leads
        leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert leads_res.status_code == 200
        leads_data = leads_res.json()["leads"]
        assert len(leads_data) >= 1

        first_lead = leads_data[0]
        lead_id = first_lead["lead_id"]

        # Verify AI recommendation default state
        assert first_lead["status"] in ["PENDING_REVIEW", "PROPOSED"]
        assert first_lead["status"] != "APPROVED"  # Safety rule check!

        # 3. Test POST /api/leads/{lead_id}/approve
        approve_res = await ac.post(f"/api/leads/{lead_id}/approve", json={
            "investigator_id": "OFFICER-4099",
            "reason": "Geotags cross-referenced with CDR records; approved for action."
        })
        assert approve_res.status_code == 200
        app_data = approve_res.json()
        assert app_data["status"] == "APPROVED"
        assert app_data["reviewed_by"] == "OFFICER-4099"
        assert app_data["provenance_type"] == "HUMAN_INVESTIGATOR_DECISION"

        # Verify Audit Event in DB
        async with AsyncSessionLocal() as session:
            audit_res = await session.execute(select(AuditEvent).filter(AuditEvent.case_id == case_id))
            audits = audit_res.scalars().all()
            event_types = [a.event_type for a in audits]
            assert "LEAD_APPROVED" in event_types

            approved_audit = next(a for a in audits if a.event_type == "LEAD_APPROVED")
            assert approved_audit.actor == "OFFICER-4099"
            assert approved_audit.details["new_status"] == "APPROVED"
            assert approved_audit.details["provenance"] == "HUMAN_INVESTIGATOR_DECISION"

        # 4. Test POST /api/leads/{lead_id}/request-analysis
        analysis_res = await ac.post(f"/api/leads/{lead_id}/request-analysis", json={
            "investigator_id": "OFFICER-4099",
            "reason": "Need additional IP geolocation analysis before final decision."
        })
        assert analysis_res.status_code == 200
        ana_data = analysis_res.json()
        assert ana_data["status"] == "NEEDS_MORE_ANALYSIS"

        # 5. Test POST /api/leads/{lead_id}/reject
        reject_res = await ac.post(f"/api/leads/{lead_id}/reject", json={
            "investigator_id": "OFFICER-4099",
            "reason": "Replaced by secondary corroborated lead."
        })
        assert reject_res.status_code == 200
        rej_data = reject_res.json()
        assert rej_data["status"] == "REJECTED"

        # Verify Audit Events in DB & via GET /api/cases/{case_id}/audit API
        audit_api_res = await ac.get(f"/api/cases/{case_id}/audit")
        assert audit_api_res.status_code == 200
        audit_api_data = audit_api_res.json()
        assert len(audit_api_data) >= 3
        assert all(item["case_id"] == case_id for item in audit_api_data)

        api_event_types = [item["event_type"] for item in audit_api_data]
        assert "LEAD_APPROVED" in api_event_types
        assert "LEAD_REJECTED" in api_event_types
        assert "LEAD_NEEDS_MORE_ANALYSIS" in api_event_types

        approved_item = next(item for item in audit_api_data if item["event_type"] == "LEAD_APPROVED")
        assert approved_item["actor"] == "OFFICER-4099"
        assert approved_item["details"]["action"] == "APPROVED"

        async with AsyncSessionLocal() as session:
            audit_res = await session.execute(select(AuditEvent).filter(AuditEvent.case_id == case_id))
            audits = audit_res.scalars().all()
            event_types = [a.event_type for a in audits]
            assert "LEAD_REJECTED" in event_types
            assert "LEAD_NEEDS_MORE_ANALYSIS" in event_types
