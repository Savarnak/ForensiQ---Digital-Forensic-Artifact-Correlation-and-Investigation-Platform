import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from app.main import app
from app.core.database import init_db, AsyncSessionLocal
from app.models.audit import AuditEvent
from app.models.lead import Lead

@pytest.mark.asyncio
async def test_human_review_and_immutable_audit_log_integration():
    await init_db()
    case_num = f"CASE-INTEG-HR-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Case
        c_res = await ac.post("/api/cases", json={"case_number": case_num, "title": "Integration Human Review Test"})
        assert c_res.status_code == 201
        case_id = c_res.json()["id"]

        # Add Evidence & Orchestrate
        await ac.post(f"/api/cases/{case_id}/evidence", data={"file_type": "CHAT_LOG"}, files={"file": ("chat.txt", b"@CyberHawk meeting with @NightOwl.", "text/plain")})
        orch_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert orch_res.status_code == 200

        # Fetch leads
        leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert leads_res.status_code == 200
        leads_data = leads_res.json()["leads"]
        assert len(leads_data) >= 1
        lead_id = leads_data[0]["lead_id"]

        # Test Approve
        app_res = await ac.post(f"/api/leads/{lead_id}/approve", json={"investigator_id": "INV-8899", "reason": "Verified geotag."})
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "APPROVED"

        # Verify Immutable Audit Event in DB
        async with AsyncSessionLocal() as session:
            audit_res = await session.execute(select(AuditEvent).filter(AuditEvent.case_id == case_id))
            audits = audit_res.scalars().all()
            event_types = [a.event_type for a in audits]
            assert "LEAD_APPROVED" in event_types

            app_audit = next(a for a in audits if a.event_type == "LEAD_APPROVED")
            assert app_audit.actor == "INV-8899"
            assert app_audit.details["new_status"] == "APPROVED"
            assert app_audit.details["provenance"] == "HUMAN_INVESTIGATOR_DECISION"
