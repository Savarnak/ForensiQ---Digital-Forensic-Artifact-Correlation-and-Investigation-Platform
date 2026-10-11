import pytest
from app.evidence.gap_contradiction_engine import GapContradictionEngine, ANALYSIS_DISCLAIMER

def test_gap_and_contradiction_engine_detection():
    evidence_items = [
        {"id": "EV-1", "file_name": "chats.json", "file_type": "CHAT_LOG"}
    ]
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EV-1",
            "content": {"text": "Referenced device DEV-D7 and file photo_99.jpg."},
            "provenance": {"source_evidence": "chats.json"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-1",
            "content": {"datetime_original": "2026-08-10 18:30:00"},
            "provenance": {"source_evidence": "photo1.jpg"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-1",
            "content": {"datetime_original": "2026-08-10 19:10:00"},
            "provenance": {"source_evidence": "photo1.jpg"}
        }
    ]

    gaps = GapContradictionEngine.detect_evidence_gaps(evidence_items, raw_findings)
    assert len(gaps) >= 1

    contradictions = GapContradictionEngine.detect_contradictions(evidence_items, raw_findings)
    assert len(contradictions) >= 1

    analysis = GapContradictionEngine.analyze_case("CASE-TEST-100", evidence_items, raw_findings)
    assert analysis["disclaimer"] == ANALYSIS_DISCLAIMER
    assert analysis["total_gaps"] >= 1
    assert analysis["total_contradictions"] >= 1
