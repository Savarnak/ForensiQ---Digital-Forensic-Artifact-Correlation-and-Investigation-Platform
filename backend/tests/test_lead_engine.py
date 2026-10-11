import pytest
import uuid
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.evidence.lead_engine import LeadEngine, InvestigativeLead
from app.models.lead import LEAD_DISCLAIMER_TEXT

SYNTHETIC_CASE_DIR = "./data/synthetic_cases/case_001"

def test_lead_engine_generation_and_explainable_priority():
    evidence_items = [
        {"id": "EV-1", "file_name": "chats.json", "file_type": "CHAT_LOG"},
        {"id": "EV-2", "file_name": "calls.csv", "file_type": "CDR"},
        {"id": "EV-3", "file_name": "gps.csv", "file_type": "GPS_LOG"},
        {"id": "EV-4", "file_name": "evidence_photo_01.jpg", "file_type": "IMAGE"}
    ]
    findings = [
        {"tool_name": "TextEntityExtractor", "evidence_id": "EV-1", "content": {"entities": [{"type": "HANDLE", "value": "@CyberHawk"}]}},
        {"tool_name": "MetadataExtractor", "evidence_id": "EV-4", "content": {"device_model": "Samsung Galaxy S22", "gps_coordinates": {"latitude": 37.774929, "longitude": -122.419416}}}
    ]
    relationships = [
        {"source": "account_cyberhawk", "target": "device_samsung_galaxy_s22", "relationship": "USES"},
        {"source": "device_samsung_galaxy_s22", "target": "loc_37.774929_-122.419416", "relationship": "LOCATED_AT"}
    ]
    timeline_events = [
        {"timestamp": "2026-08-10T14:00:00Z", "location": "San Francisco Dock 14"},
        {"timestamp": "2026-08-10T14:05:30Z", "location": "GPS (37.774929, -122.419416)"}
    ]
    evidence_gaps = [
        {"referenced_entity": "DEV-D7", "reason": "Referenced device missing from evidence repository"}
    ]
    contradictions = [
        {"contradiction_type": "CONFLICTING_TIMESTAMPS"}
    ]

    leads = LeadEngine.generate_leads(
        case_id="TEST-CASE-100",
        findings=findings,
        relationships=relationships,
        timeline_events=timeline_events,
        evidence_gaps=evidence_gaps,
        contradictions=contradictions,
        evidence_items=evidence_items
    )

    assert len(leads) >= 1

    for lead in leads:
        # Verify required schema fields
        assert lead.lead_id.startswith("LEAD-")
        assert lead.case_id == "TEST-CASE-100"
        assert lead.priority in ["HIGH", "MEDIUM", "LOW"]
        assert lead.status in ["PENDING_REVIEW", "PROPOSED"]
        assert lead.confidence >= 0.50

        # Verify transparent reasoning factors (NO opaque AI claims)
        assert len(lead.reasoning_factors) >= 1
        for factor in lead.reasoning_factors:
            assert "AI says" not in factor
            assert "high risk prediction" not in factor

        # Verify legal non-guilt disclaimer
        assert lead.disclaimer == LEAD_DISCLAIMER_TEXT
        assert "not constitute a determination of guilt" in lead.disclaimer

def test_explainable_priority_scoring_rules():
    # 3+ factors -> HIGH
    p1, factors1, conf1 = LeadEngine.calculate_priority_and_factors(
        evidence_sources=["chats.json", "calls.csv", "gps.csv", "photo.jpg"],
        relationships=[{"relationship": "USES"}, {"relationship": "LOCATED_AT"}],
        timeline_events=[{"ts": 1}, {"ts": 2}],
        has_device_link=True,
        has_location_link=True,
        has_gap_or_conflict=True
    )
    assert p1 == "HIGH"
    assert "supporting evidence from 4 independent artifacts" in factors1
    assert "same device associated with multiple evidence artifacts" in factors1

    # 1 factor -> LOW
    p2, factors2, conf2 = LeadEngine.calculate_priority_and_factors(
        evidence_sources=["doc.txt"],
        relationships=[],
        timeline_events=[],
        has_device_link=False,
        has_location_link=False,
        has_gap_or_conflict=False
    )
    assert p2 == "LOW"

@pytest.mark.asyncio
async def test_get_case_leads_api_endpoint():
    await init_db()
    unique_num = f"CASE-2026-LEADS-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Case
        case_res = await ac.post("/api/cases", json={
            "case_number": unique_num,
            "title": "Operation Cygnus - Lead Engine Test",
            "description": "Testing ARGUS Investigative Lead Engine API"
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # 2. Add Evidence
        ev_res = await ac.post(f"/api/cases/{case_id}/evidence", data={"file_type": "CHAT_LOG"}, files={"file": ("chat_evidence.txt", b"@CyberHawk meeting with @NightOwl.", "text/plain")})
        assert ev_res.status_code == 201

        # 3. GET Leads API
        leads_res = await ac.get(f"/api/cases/{case_id}/leads")
        assert leads_res.status_code == 200

        data = leads_res.json()
        assert data["status"] == "success"
        assert data["case_id"] == case_id
        assert "total_leads" in data
        assert "leads" in data
        assert len(data["leads"]) >= 1

        first_lead = data["leads"][0]
        assert "lead_id" in first_lead
        assert "priority" in first_lead
        assert "reasoning_factors" in first_lead
        assert "disclaimer" in first_lead
        assert first_lead["priority"] in ["HIGH", "MEDIUM", "LOW"]
        assert first_lead["disclaimer"] == LEAD_DISCLAIMER_TEXT
