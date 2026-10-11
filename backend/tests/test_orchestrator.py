import pytest
from app.orchestrator.state import CaseState
from app.orchestrator.brain_graph import investigation_graph

@pytest.mark.asyncio
async def test_langgraph_pipeline_execution():
    initial_state = CaseState(
        case_id="CASE-TEST-100",
        case_number="CASE-2026-TEST",
        investigation_goal="Identify handles and geotags",
        evidence_items=[
            {
                "id": "EV-001",
                "file_name": "synthetic_chat_log.txt",
                "file_path": "./data/synthetic/synthetic_chat_log.txt",
                "file_type": "CHAT_LOG",
                "text_content": "@CyberHawk sent message to @NightOwl at +1-555-0199."
            }
        ]
    )

    final_state_dict = await investigation_graph.ainvoke(initial_state.dict())
    
    assert len(final_state_dict["tasks"]) > 0
    assert len(final_state_dict["raw_findings"]) > 0
    assert len(final_state_dict["proposed_leads"]) > 0
    assert final_state_dict["proposed_leads"][0]["status"] == "PROPOSED"

@pytest.mark.asyncio
async def test_orchestrator_get_results_case_isolation():
    import uuid
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.database import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        case_res = await ac.post("/api/cases", json={
            "case_number": f"CASE-2026-ISOLATION-{str(uuid.uuid4())[:6]}",
            "title": "Isolation Test Case"
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # 1. New case with no runs should return None/null for orchestrator results
        res1 = await ac.get(f"/api/orchestrator/results/{case_id}")
        assert res1.status_code == 200
        assert res1.json() is None

        # 2. Run investigation
        run_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert run_res.status_code == 200

        # 3. Fetch results for case_id
        res2 = await ac.get(f"/api/orchestrator/results/{case_id}")
        assert res2.status_code == 200
        data = res2.json()
        assert data is not None
        assert data["status"] == "success"
        assert data["investigation_run"]["case_id"] == case_id

@pytest.mark.asyncio
async def test_synthetic_cygnus_knowledge_graph_and_provenance():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.database import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Load synthetic CYGNUS case
        synth_res = await ac.post("/api/cases/synthetic")
        assert synth_res.status_code in [200, 201]
        cygnus_case = synth_res.json()
        case_id = cygnus_case["id"]
        assert cygnus_case["case_number"] == "CASE-2026-CYGNUS"

        # 2. Trigger Orchestrator Run on CYGNUS case
        run_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert run_res.status_code == 200
        run_data = run_res.json()

        kg = run_data["correlations"]["knowledge_graph"]
        nodes = kg["nodes"]
        edges = kg["edges"]

        # Assertion 1: CYGNUS produces >0 canonical entities beyond raw evidence nodes
        non_evidence_nodes = [n for n in nodes if n.get("label") != "Evidence"]
        assert len(nodes) > 9
        assert len(non_evidence_nodes) > 0

        # Assertion 2: CYGNUS produces >0 evidence-backed relationships
        assert len(edges) > 0

        # Assertion 3: Relationships contain valid source evidence provenance
        for edge in edges:
            assert "supporting_evidence" in edge or "properties" in edge
            ev_list = edge.get("supporting_evidence") or edge.get("properties", {}).get("supporting_evidence", [])
            assert len(ev_list) > 0
            assert "file_name" in ev_list[0]

        # Assertion 4: Case-isolation verification - no cross-case contamination
        results_res = await ac.get(f"/api/orchestrator/results/{case_id}")
        assert results_res.status_code == 200
        fetched_data = results_res.json()
        assert fetched_data["investigation_run"]["case_id"] == case_id
        assert len(fetched_data["correlations"]["knowledge_graph"]["edges"]) > 0

        # Assertion 5: Lead persistence & approval consistency check
        assert len(run_data["leads"]) >= 1
        target_lead = run_data["leads"][0]
        target_lead_id = target_lead.get("id") or target_lead.get("lead_id")

        get_leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert get_leads_res.status_code == 200
        fetched_leads = get_leads_res.json()["leads"]
        fetched_ids = [l.get("lead_id") or l.get("id") for l in fetched_leads]
        assert target_lead_id in fetched_ids

        # Approve lead using exact ID returned by run/GET endpoints
        app_res = await ac.post(f"/api/leads/{target_lead_id}/approve", json={
            "investigator_id": "OFFICER-CYGNUS",
            "reason": "Verified cross-source correlation; approved."
        })
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "APPROVED"

        # Verify AuditEvent exists for approved lead
        audit_res = await ac.get(f"/api/cases/{case_id}/audit")
        assert audit_res.status_code == 200
        audit_events = audit_res.json()
        assert any(e["event_type"] == "LEAD_APPROVED" and e["details"]["lead_id"] == target_lead_id for e in audit_events)

@pytest.mark.asyncio
async def test_investigation_run_findings_deduplication_and_task_uniqueness():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.database import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Load synthetic case
        synth_res = await ac.post("/api/cases/synthetic")
        cygnus_case = synth_res.json()
        case_id = cygnus_case["id"]

        # 2. Run initial investigation (Run 1)
        run1_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert run1_res.status_code == 200
        run1_data = run1_res.json()

        run1_id = run1_data["investigation_run"]["id"]
        run1_tasks = run1_data["tasks"]
        run1_findings = run1_data["findings"]["raw"]
        run1_count = run1_data["findings"]["count"]

        # Assertion A: Task IDs must be strictly unique within an investigation run
        task_ids = [t["id"] if "id" in t else t.get("task_id") for t in run1_tasks]
        # Filter non-None
        task_ids = [tid for tid in task_ids if tid]
        assert len(task_ids) == len(set(task_ids)), f"Duplicate task IDs found: {task_ids}"

        # Assertion B: Finite, deterministic finding count (not inflated by missing evidence target matching)
        assert run1_count > 0
        assert run1_count == len(run1_findings)
        assert run1_count < 100, f"Findings count ({run1_count}) unexpectedly high, possible duplicate accumulation"

        # Assertion C: Repeated evidence/tool combinations are deduplicated
        finding_keys = [
            f"{f['evidence_id']}_{f['tool_name']}_{f['finding_type']}_{hash(str(f['content']))}"
            for f in run1_findings
        ]
        assert len(finding_keys) == len(set(finding_keys)), "Duplicate findings detected within single run"

        # 3. Perform second intentional investigation run (Run 2)
        run2_res = await ac.post(f"/api/orchestrator/run/{case_id}")
        assert run2_res.status_code == 200
        run2_data = run2_res.json()

        run2_id = run2_data["investigation_run"]["id"]
        run2_count = run2_data["findings"]["count"]

        # Assertion D: Each run produces a unique run_id
        assert run1_id != run2_id

        # Assertion E: Second run does NOT accumulate/inflate findings from first run
        assert run2_count == run1_count, f"Run 2 count ({run2_count}) mismatched Run 1 count ({run1_count}) due to accumulation"

        # Assertion F: GET /api/orchestrator/results/{case_id} returns exact unique findings count
        results_res = await ac.get(f"/api/orchestrator/results/{case_id}")
        assert results_res.status_code == 200
        fetched_count = results_res.json()["findings"]["count"]
        assert fetched_count == run2_count

