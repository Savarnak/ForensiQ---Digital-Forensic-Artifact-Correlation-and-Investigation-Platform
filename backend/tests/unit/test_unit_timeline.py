import pytest
from app.evidence.timeline_engine import TimelineEngine, TimelineEvent

def test_timeline_engine_merging_and_anomalies():
    events = [
        TimelineEvent(
            timestamp="2026-08-10T14:00:00Z",
            event_type="CHAT_MESSAGE",
            description="Chat message CHAT-1001",
            explanation="Parsed from chats.json",
            location="San Francisco Dock 14",
            source_evidence="chats.json",
            source_tool="ChatParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:00:30Z",
            event_type="GPS_PING",
            description="GPS ping at Dock 14",
            explanation="Parsed from gps.csv",
            location="San Francisco Dock 14",
            source_evidence="gps.csv",
            source_tool="GPSParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:01:00Z",
            event_type="CELL_CALL",
            description="Cell call from tower OAK",
            explanation="Parsed from calls.csv",
            location="Oakland Tower 202",
            source_evidence="calls.csv",
            source_tool="CDRParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:25:00Z",
            event_type="CHAT_MESSAGE",
            description="Late chat message",
            explanation="Parsed from chats.json",
            source_evidence="chats.json",
            source_tool="ChatParser"
        )
    ]

    anomaly_results = TimelineEngine.detect_anomalies(events)

    assert len(anomaly_results["temporal_overlaps"]) >= 1
    assert len(anomaly_results["conflicting_timestamps"]) >= 1
    assert len(anomaly_results["suspicious_gaps"]) >= 1

    for e in events:
        assert isinstance(e.explanation, str) and len(e.explanation) > 0
        assert e.confidence > 0.0
