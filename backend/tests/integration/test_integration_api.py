import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

@pytest.mark.asyncio
async def test_rest_api_payload_contract_compliance():
    await init_db()
    case_num = f"CASE-INTEG-API-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Health check
        h_res = await ac.get("/api/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] in ["healthy", "ok"]

        # Create case
        c_res = await ac.post("/api/cases", json={"case_number": case_num, "title": "API Contract Compliance Test"})
        assert c_res.status_code == 201
        case_id = c_res.json()["id"]

        # Add Goal
        g_res = await ac.post(f"/api/cases/{case_id}/goals", json={"goal_text": "Verify API contracts", "status": "ACTIVE"})
        assert g_res.status_code == 201

        # Get Goal
        g_list = await ac.get(f"/api/cases/{case_id}/goals")
        assert g_list.status_code == 200
        assert len(g_list.json()) >= 1

        # Get Timeline
        t_res = await ac.get(f"/api/cases/{case_id}/timeline")
        assert t_res.status_code == 200
        assert "timeline" in t_res.json()

        # Get Gaps
        gap_res = await ac.get(f"/api/cases/{case_id}/analysis/gaps-contradictions")
        assert gap_res.status_code == 200
        assert "evidence_gaps" in gap_res.json()
