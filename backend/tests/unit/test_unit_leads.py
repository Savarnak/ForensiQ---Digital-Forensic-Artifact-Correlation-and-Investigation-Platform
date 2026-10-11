import pytest
from app.evidence.lead_engine import LeadEngine
from app.models.lead import LEAD_DISCLAIMER_TEXT

def test_lead_engine_priority_and_transparent_factors():
    evidence_sources = ["chats.json", "calls.csv", "gps.csv", "evidence_photo_01.jpg"]
    relationships = [{"relationship": "USES"}, {"relationship": "LOCATED_AT"}]
    timeline_events = [{"timestamp": "2026-08-10T14:00:00Z"}, {"timestamp": "2026-08-10T14:05:30Z"}]

    priority, factors, confidence = LeadEngine.calculate_priority_and_factors(
        evidence_sources=evidence_sources,
        relationships=relationships,
        timeline_events=timeline_events,
        has_device_link=True,
        has_location_link=True,
        has_gap_or_conflict=True
    )

    assert priority == "HIGH"
    assert confidence >= 0.80
    assert len(factors) >= 3

    for f in factors:
        assert "AI says" not in f
        assert "blackbox" not in f

    leads = LeadEngine.generate_leads(
        case_id="CASE-UNIT-100",
        findings=[],
        relationships=relationships,
        timeline_events=timeline_events,
        evidence_gaps=[{"referenced_entity": "DEV-D7"}],
        contradictions=[],
        evidence_items=[{"file_name": s} for s in evidence_sources]
    )

    assert len(leads) >= 1
    for l in leads:
        assert l.status == "PENDING_REVIEW"
        assert l.disclaimer == LEAD_DISCLAIMER_TEXT
