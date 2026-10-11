import pytest
from app.tools.registry import tool_registry, StandardizedFinding, BaseInvestigativeTool

def test_tool_registry_registration_and_lookup():
    tools = tool_registry.list_tools()
    assert len(tools) >= 5

    names = [t["name"] for t in tools]
    assert "TextEntityExtractor" in names
    assert "OCRTool" in names
    assert "MetadataExtractor" in names
    assert "EvidenceSearchTool" in names
    assert "TimelineExtractor" in names

def test_find_by_capability():
    entity_tools = tool_registry.find_by_capability("entity_extraction")
    assert len(entity_tools) >= 1
    assert any(t.name == "TextEntityExtractor" for t in entity_tools)

    metadata_tools = tool_registry.find_by_capability("metadata_extraction")
    assert len(metadata_tools) >= 1
    assert any(t.name == "MetadataExtractor" for t in metadata_tools)

    ocr_tools = tool_registry.find_by_capability("ocr")
    assert len(ocr_tools) >= 1
    assert any(t.name == "OCRTool" for t in ocr_tools)

    timeline_tools = tool_registry.find_by_capability("timeline_extraction")
    assert len(timeline_tools) >= 1
    assert any(t.name == "TimelineExtractor" for t in timeline_tools)

def test_standardized_finding_schema():
    finding = StandardizedFinding(
        case_id="CASE-001",
        evidence_id="EV-100",
        finding_type="ENTITY_EXTRACTED",
        entity_type="HANDLE",
        entity="@CyberHawk",
        attribute="handle_name",
        value="@CyberHawk",
        confidence=0.95,
        source_tool="TextEntityExtractor",
        supporting_evidence={"file_name": "chats.json#CHAT-1001"}
    )

    data = finding.model_dump() if hasattr(finding, "model_dump") else finding.dict()
    assert data["case_id"] == "CASE-001"
    assert data["entity"] == "@CyberHawk"
    assert data["confidence"] == 0.95
    assert "finding_id" in data
    assert "timestamp" in data
