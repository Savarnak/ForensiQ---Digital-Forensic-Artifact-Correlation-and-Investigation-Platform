import pytest
import os
import json
import csv
from app.correlation.fusion_service import IntelligenceFusionService, CORRELATION_DISCLAIMER
from app.knowledge_graph.graph_builder import KnowledgeGraphBuilder, NODE_TYPES, RELATIONSHIP_TYPES

SYNTHETIC_CASE_DIR = "./data/synthetic_cases/case_001"

@pytest.fixture
def synthetic_case_data():
    """Fixture loading synthetic case_001 artifacts."""
    chats_path = os.path.join(SYNTHETIC_CASE_DIR, "chats.json")
    devices_path = os.path.join(SYNTHETIC_CASE_DIR, "devices.json")
    calls_path = os.path.join(SYNTHETIC_CASE_DIR, "calls.csv")

    chats = []
    if os.path.exists(chats_path):
        with open(chats_path, "r", encoding="utf-8") as f:
            chats = json.load(f)

    devices = []
    if os.path.exists(devices_path):
        with open(devices_path, "r", encoding="utf-8") as f:
            devices = json.load(f)

    calls = []
    if os.path.exists(calls_path):
        with open(calls_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            calls = list(reader)

    return {
        "chats": chats,
        "devices": devices,
        "calls": calls
    }

def test_canonical_node_and_relationship_types():
    assert "Case" in NODE_TYPES
    assert "Person" in NODE_TYPES
    assert "Account" in NODE_TYPES
    assert "Device" in NODE_TYPES
    assert "Location" in NODE_TYPES
    assert "Evidence" in NODE_TYPES
    assert "Event" in NODE_TYPES
    assert "VehicleObject" in NODE_TYPES

    assert "ASSOCIATED_WITH" in RELATIONSHIP_TYPES
    assert "USES" in RELATIONSHIP_TYPES
    assert "LOCATED_AT" in RELATIONSHIP_TYPES
    assert "APPEARS_IN" in RELATIONSHIP_TYPES
    assert "MENTIONED_IN" in RELATIONSHIP_TYPES
    assert "OCCURRED_AT" in RELATIONSHIP_TYPES
    assert "SUPPORTED_BY" in RELATIONSHIP_TYPES
    assert "CORRELATES_WITH" in RELATIONSHIP_TYPES

def test_entity_resolution_and_node_generation(synthetic_case_data):
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EVID-CHAT-100",
            "content": {
                "entities": [
                    {"type": "HANDLE", "value": "@CyberHawk"},
                    {"type": "PHONE", "value": "+1-555-0199"},
                    {"type": "EMAIL", "value": "alpha@fictional-domain.test"},
                    {"type": "IP_ADDRESS", "value": "192.168.1.105"}
                ]
            },
            "provenance": {"source_evidence": "chats.json"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EVID-IMG-200",
            "content": {
                "device_model": "Samsung Galaxy S22",
                "gps_coordinates": {"latitude": 37.774929, "longitude": -122.419416},
                "datetime_original": "2026-08-10 14:05:30"
            },
            "provenance": {"source_evidence": "evidence_photo_01.jpg"}
        }
    ]

    evidence_items = [
        {"id": "EVID-CHAT-100", "file_name": "chats.json", "file_type": "CHAT_LOG"},
        {"id": "EVID-IMG-200", "file_name": "evidence_photo_01.jpg", "file_type": "IMAGE"}
    ]

    nodes = IntelligenceFusionService.resolve_entities(raw_findings, evidence_items)
    assert len(nodes) >= 5

    labels = set(n["label"] for n in nodes)
    assert "Account" in labels
    assert "Device" in labels
    assert "Location" in labels
    assert "Evidence" in labels

def test_cross_evidence_correlation_patterns(synthetic_case_data):
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EVID-001",
            "content": {"entities": [{"type": "HANDLE", "value": "@CyberHawk"}]},
            "provenance": {"source_evidence": "chats.json"}
        },
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EVID-002",
            "content": {"entities": [{"type": "HANDLE", "value": "@CyberHawk"}]},
            "provenance": {"source_evidence": "social_messages.json"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EVID-003",
            "content": {
                "device_model": "Samsung Galaxy S22",
                "gps_coordinates": {"latitude": 37.774929, "longitude": -122.419416},
                "datetime_original": "2026-08-10T14:05:30Z"
            },
            "provenance": {"source_evidence": "evidence_photo_01.jpg"}
        },
        {
            "tool_name": "TimelineExtractor",
            "evidence_id": "EVID-001",
            "content": {
                "timeline_events": [
                    {"timestamp": "2026-08-10T14:05:30Z", "context": "Photo captured at SF Dock 14"}
                ]
            },
            "provenance": {"source_evidence": "chats.json"}
        }
    ]

    evidence_items = [
        {"id": "EVID-001", "file_name": "chats.json", "file_type": "CHAT_LOG"},
        {"id": "EVID-002", "file_name": "social_messages.json", "file_type": "TEXT"},
        {"id": "EVID-003", "file_name": "evidence_photo_01.jpg", "file_type": "IMAGE"}
    ]

    nodes = IntelligenceFusionService.resolve_entities(raw_findings, evidence_items)
    results = IntelligenceFusionService.detect_relationships_and_correlations(raw_findings, evidence_items, nodes)

    correlations = results["correlations"]
    assert len(correlations) >= 1

    patterns_detected = set(c["pattern"] for c in correlations)
    assert "SAME_ENTITY_ACROSS_EVIDENCE" in patterns_detected or "REPEATED_ACCOUNT" in patterns_detected

    # Verify non-guilt disclaimer on every correlation finding
    for c in correlations:
        assert c["disclaimer"] == CORRELATION_DISCLAIMER

    # Verify relationship edges contain disclaimer and valid types
    for edge in results["edges"]:
        assert edge["disclaimer"] == CORRELATION_DISCLAIMER
        assert edge["relationship"] in RELATIONSHIP_TYPES

    # Verify timeline construction
    assert len(results["timeline_events"]) >= 1
