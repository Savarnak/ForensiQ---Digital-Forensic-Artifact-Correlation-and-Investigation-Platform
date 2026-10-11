import pytest
from app.correlation.fusion_service import IntelligenceFusionService, CORRELATION_DISCLAIMER
from app.knowledge_graph.graph_builder import KnowledgeGraphBuilder, NODE_TYPES, RELATIONSHIP_TYPES

def test_intelligence_fusion_entity_resolution():
    raw_findings = [
        {
            "tool_name": "TextEntityExtractor",
            "evidence_id": "EV-CHAT-1",
            "content": {
                "entities": [
                    {"type": "HANDLE", "value": "@CyberHawk"},
                    {"type": "PHONE", "value": "+1-555-0199"},
                    {"type": "IP_ADDRESS", "value": "192.168.1.105"}
                ]
            },
            "provenance": {"source_evidence": "chats.json"}
        },
        {
            "tool_name": "MetadataExtractor",
            "evidence_id": "EV-IMG-1",
            "content": {
                "device_model": "Samsung Galaxy S22",
                "gps_coordinates": {"latitude": 37.774929, "longitude": -122.419416}
            },
            "provenance": {"source_evidence": "evidence_photo_01.jpg"}
        }
    ]

    evidence_items = [
        {"id": "EV-CHAT-1", "file_name": "chats.json"},
        {"id": "EV-IMG-1", "file_name": "evidence_photo_01.jpg"}
    ]

    nodes = IntelligenceFusionService.resolve_entities(raw_findings, evidence_items)
    results = IntelligenceFusionService.detect_relationships_and_correlations(raw_findings, evidence_items, nodes)

    node_labels = set(n["label"] for n in nodes)
    assert "Account" in node_labels
    assert "Person" in node_labels
    assert "Device" in node_labels
    assert "Location" in node_labels
    assert "Evidence" in node_labels

    edges = results["edges"]
    assert len(edges) >= 1
    for edge in edges:
        assert edge["relationship"] in RELATIONSHIP_TYPES
        assert edge["disclaimer"] == CORRELATION_DISCLAIMER
