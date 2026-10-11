import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

@pytest.mark.asyncio
async def test_phase1_case_and_subresource_apis():
    await init_db()
    unique_num = f"CASE-2026-TEST-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Case
        case_payload = {
            "case_number": unique_num,
            "title": "Phase 1 Foundation Test Case",
            "description": "Testing core domain models and APIs"
        }
        res = await ac.post("/api/cases", json=case_payload)
        assert res.status_code == 201, f"Create Case failed: {res.text}"
        case_data = res.json()
        case_id = case_data["id"]
        assert case_data["case_number"] == unique_num

        # 2. List Cases
        res = await ac.get("/api/cases")
        assert res.status_code == 200, f"List Cases failed: {res.text}"
        cases_list = res.json()
        assert any(c["id"] == case_id for c in cases_list)

        # 3. Get Case By ID
        res = await ac.get(f"/api/cases/{case_id}")
        assert res.status_code == 200, f"Get Case failed: {res.text}"
        assert res.json()["id"] == case_id

        # 4. Add Investigation Goal
        goal_payload = {
            "goal_text": "Identify suspect handles and reconstruct timeline.",
            "priority": "HIGH"
        }
        res = await ac.post(f"/api/cases/{case_id}/goals", json=goal_payload)
        assert res.status_code == 201, f"Create Goal failed: {res.text}"
        goal_data = res.json()
        assert goal_data["case_id"] == case_id
        assert goal_data["goal_text"] == goal_payload["goal_text"]

        # 5. List Goals
        res = await ac.get(f"/api/cases/{case_id}/goals")
        assert res.status_code == 200, f"List Goals failed: {res.text}"
        assert len(res.json()) >= 1

        # 6. Upload Evidence
        files = {"file": ("test_file.txt", b"Sample test content for Phase 1 evidence", "text/plain")}
        data = {"file_type": "CHAT_LOG"}
        res = await ac.post(f"/api/cases/{case_id}/evidence", data=data, files=files)
        assert res.status_code == 201, f"Upload Evidence failed: {res.text}"
        ev_data = res.json()
        assert ev_data["case_id"] == case_id
        assert ev_data["file_name"] == "test_file.txt"

        # 7. List Evidence
        res = await ac.get(f"/api/cases/{case_id}/evidence")
        assert res.status_code == 200, f"List Evidence failed: {res.text}"
        assert len(res.json()) >= 1

        # 8. Initialize Investigation Run
        res = await ac.post(f"/api/cases/{case_id}/investigations", json={"goal_id": goal_data["id"]})
        assert res.status_code == 201, f"Create Investigation failed: {res.text}"
        run_data = res.json()
        assert run_data["case_id"] == case_id

        # 9. List Investigation Runs
        res = await ac.get(f"/api/cases/{case_id}/investigations")
        assert res.status_code == 200, f"List Investigations failed: {res.text}"
        assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_load_synthetic_case_endpoint_regression():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/cases/synthetic")
        assert res.status_code in [200, 201], f"Load Synthetic Case failed: {res.text}"
        case_data = res.json()
        assert case_data["case_number"] == "CASE-2026-CYGNUS"
        case_id = case_data["id"]

        # Verify evidence loaded automatically
        ev_res = await ac.get(f"/api/cases/{case_id}/evidence")
        assert ev_res.status_code == 200
        ev_items = ev_res.json()
        assert len(ev_items) >= 4, f"Expected at least 4 synthetic evidence files, got {len(ev_items)}"

        # Verify goal loaded automatically
        goal_res = await ac.get(f"/api/cases/{case_id}/goals")
        assert goal_res.status_code == 200
        goals = goal_res.json()
        assert len(goals) >= 1

@pytest.mark.asyncio
async def test_synthetic_case_response_headers_and_contract():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/cases/synthetic", headers={"Content-Type": "application/json"})
        assert res.status_code in [200, 201]
        assert "application/json" in res.headers.get("content-type", "").lower()
        assert len(res.content) > 0
        data = res.json()
        assert "id" in data
        assert data["case_number"] == "CASE-2026-CYGNUS"

        case_id = data["id"]
        leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert leads_res.status_code == 200
        assert "application/json" in leads_res.headers.get("content-type", "").lower()
        assert len(leads_res.content) > 0
        leads_data = leads_res.json()
        assert isinstance(leads_data, dict) or isinstance(leads_data, list)


