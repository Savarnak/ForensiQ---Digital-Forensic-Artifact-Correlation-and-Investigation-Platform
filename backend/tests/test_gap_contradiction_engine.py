import pytest
import uuid
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.evidence.gap_contradiction_engine import GapContradictionEngine, ANALYSIS_DISCLAIMER

SYNTHETIC_CASE_DIR = "./data/synthetic_cases/case_001"

def test_detect_evidence_gaps_referenced_missing_device():
    evidence_items = [
        {"id": "EV-1", "file_name": "chats.json", "file_type": "CHAT_LOG"}
    ]
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EV-1",
            "content": {
                "text": "Confirmed connection from device DEV-D7 and file evidence_photo_99.jpg at location SF Dock 14."
            },
            "provenance": {"source_evidence": "chats.json"}
        }
    ]

    gaps = GapContradictionEngine.detect_evidence_gaps(evidence_items, raw_findings, synthetic_case_dir=SYNTHETIC_CASE_DIR)
    assert len(gaps) >= 1

    gap_entities = set(g.referenced_entity for g in gaps)
    assert "DEV-D7" in gap_entities or "evidence_photo_99.jpg" in gap_entities

    for gap in gaps:
        assert gap.confidence >= 0.80
        assert len(gap.recommended_action) > 0
        assert len(gap.supporting_evidence) >= 1

def test_detect_contradictions_timestamps_and_attributes():
    evidence_items = [
        {"id": "EV-1", "file_name": "photo1.jpg", "file_type": "IMAGE"},
        {"id": "EV-2", "file_name": "photo2.jpg", "file_type": "IMAGE"}
    ]
    raw_findings = [
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-1",
            "content": {"datetime_original": "2026-08-10 18:30:00", "device_model": "iPhone 14"},
            "provenance": {"source_evidence": "photo1.jpg"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-2",
            "content": {"datetime_original": "2026-08-10 19:10:00", "device_model": "iPhone 14"},
            "provenance": {"source_evidence": "photo2.jpg"}
        }
    ]

    contradictions = GapContradictionEngine.detect_contradictions(evidence_items, raw_findings, synthetic_case_dir=SYNTHETIC_CASE_DIR)
    assert len(contradictions) >= 1

    for c in contradictions:
        assert c.confidence >= 0.80
        assert len(c.recommended_investigator_action) > 0
        assert c.evidence_item_1 is not None
        assert c.evidence_item_2 is not None

def test_detect_chain_issues():
    evidence_items = [{"id": "EV-1", "file_name": "social.json"}]
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EV-1",
            "content": {"entities": [{"type": "HANDLE", "value": "@UnverifiedPeer"}]},
            "provenance": {"source_evidence": "social_messages.json"}
        }
    ]

    issues = GapContradictionEngine.detect_chain_issues(evidence_items, raw_findings, synthetic_case_dir=SYNTHETIC_CASE_DIR)
    assert len(issues) >= 1

    subjects = [i.subject for i in issues]
    assert "@UnverifiedPeer" in subjects or any("DEV-MAC" in s for s in subjects)

@pytest.mark.asyncio
async def test_get_case_gaps_and_contradictions_api_endpoint():
    await init_db()
    unique_num = f"CASE-2026-ANALYSIS-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Case
        case_res = await ac.post("/api/cases", json={
            "case_number": unique_num,
            "title": "Operation Cygnus - Gap Analysis Test",
            "description": "Testing ARGUS Evidence Gap & Contradiction API"
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # 2. Add Evidence
        ev_res = await ac.post(f"/api/cases/{case_id}/evidence", data={"file_type": "CHAT_LOG"}, files={"file": ("chat_evidence.txt", b"Referenced device DEV-D7.", "text/plain")})
        assert ev_res.status_code == 201

        # 3. GET Gaps and Contradictions API
        analysis_res = await ac.get(f"/api/cases/{case_id}/analysis/gaps-contradictions")
        assert analysis_res.status_code == 200

        data = analysis_res.json()
        assert data["status"] == "success"
        assert data["case_id"] == case_id
        assert "total_gaps" in data
        assert "total_contradictions" in data
        assert "total_chain_issues" in data
        assert "evidence_gaps" in data
        assert "contradictions" in data
        assert "investigation_chain_issues" in data
        assert data["disclaimer"] == ANALYSIS_DISCLAIMER
