import pytest
import uuid
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.evidence.timeline_engine import TimelineEngine, TimelineEvent

SYNTHETIC_CASE_DIR = "./data/synthetic_cases/case_001"

def test_timeline_engine_event_merging_and_required_fields():
    evidence_items = [
        {"id": "EV-1", "file_name": "chats.json", "file_type": "CHAT_LOG"},
        {"id": "EV-2", "file_name": "evidence_photo_01.jpg", "file_type": "IMAGE"}
    ]
    raw_findings = [
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-2",
            "content": {
                "datetime_original": "2026-08-10 14:05:30",
                "device_model": "Samsung Galaxy S22",
                "gps_coordinates": {"latitude": 37.774929, "longitude": -122.419416}
            },
            "provenance": {"source_evidence": "evidence_photo_01.jpg"}
        }
    ]

    result = TimelineEngine.build_timeline(
        evidence_items=evidence_items,
        raw_findings=raw_findings,
        synthetic_case_dir=SYNTHETIC_CASE_DIR if os.path.exists(SYNTHETIC_CASE_DIR) else None
    )

    assert result["total_events"] >= 1
    timeline = result["timeline"]

    # Verify required fields on every timeline event
    for event in timeline:
        assert "event_id" in event
        assert "timestamp" in event
        assert "event_type" in event
        assert "description" in event
        assert "explanation" in event
        assert "entities" in event
        assert "source_evidence" in event
        assert "source_tool" in event
        assert "confidence" in event
        assert isinstance(event["explanation"], str) and len(event["explanation"]) > 0

def test_timeline_engine_anomaly_detection():
    events = [
        TimelineEvent(
            timestamp="2026-08-10T14:00:00Z",
            event_type="CHAT_MESSAGE",
            description="Chat CHAT-1001",
            explanation="Test chat event",
            location="San Francisco Dock 14",
            source_evidence="chats.json",
            source_tool="ChatParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:00:30Z",
            event_type="GPS_PING",
            description="GPS Ping Dock 14",
            explanation="Test GPS event",
            location="San Francisco Dock 14",
            source_evidence="gps.csv",
            source_tool="GPSParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:01:00Z",
            event_type="CELL_CALL",
            description="Call from tower OAK",
            explanation="Test CDR event",
            location="Oakland Tower 202",
            source_evidence="calls.csv",
            source_tool="CDRParser"
        ),
        TimelineEvent(
            timestamp="2026-08-10T14:25:00Z",
            event_type="CHAT_MESSAGE",
            description="Later chat message",
            explanation="Late event after gap",
            source_evidence="chats.json",
            source_tool="ChatParser"
        )
    ]

    anomaly_results = TimelineEngine.detect_anomalies(events)

    assert len(anomaly_results["temporal_overlaps"]) >= 1
    assert len(anomaly_results["conflicting_timestamps"]) >= 1
    assert len(anomaly_results["suspicious_gaps"]) >= 1

@pytest.mark.asyncio
async def test_get_case_timeline_api_endpoint():
    await init_db()
    unique_num = f"CASE-2026-TIMELINE-{str(uuid.uuid4())[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Case
        case_res = await ac.post("/api/cases", json={
            "case_number": unique_num,
            "title": "Operation Cygnus - Timeline Test",
            "description": "Testing ARGUS timeline engine API"
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # 2. Add Evidence
        ev_res = await ac.post(f"/api/cases/{case_id}/evidence", data={"file_type": "CHAT_LOG"}, files={"file": ("chat_evidence.txt", b"Sample chat content", "text/plain")})
        assert ev_res.status_code == 201

        # 3. GET Timeline
        timeline_res = await ac.get(f"/api/cases/{case_id}/timeline")
        assert timeline_res.status_code == 200

        data = timeline_res.json()
        assert data["status"] == "success"
        assert data["case_id"] == case_id
        assert "total_events" in data
        assert "timeline" in data
        assert "temporal_overlaps" in data
        assert "suspicious_gaps" in data
        assert "conflicting_timestamps" in data
        assert "analysis_summary" in data
