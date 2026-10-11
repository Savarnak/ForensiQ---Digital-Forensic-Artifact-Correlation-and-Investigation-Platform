import pytest
import os
import tempfile
from app.tools.registry import (
    ToolRegistry,
    AgentRegistry,
    tool_registry,
    BaseInvestigativeTool,
    ToolInputSchema,
    ToolOutputSchema,
    StandardizedFinding
)
from app.tools import (
    TextEntityExtractor,
    OCRTool,
    MetadataExtractor,
    EvidenceSearchTool,
    TimelineExtractor
)

def test_registry_registration_and_unregistration():
    local_registry = ToolRegistry()

    class CustomTestTool(BaseInvestigativeTool):
        name = "custom_test_tool"
        description = "A dummy tool for unit testing registry registration."
        supported_input_types = ["TEXT"]
        capabilities = ["custom_test_capability"]

        async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
            return ToolOutputSchema(
                tool_name=self.name,
                success=True,
                findings_extracted=0,
                data={}
            )

    # 1. Register tool class
    registered_instance = local_registry.register(CustomTestTool)
    assert registered_instance is not None
    assert local_registry.get("custom_test_tool") is not None

    # 2. List tools
    tool_list = local_registry.list()
    assert any(t["name"] == "custom_test_tool" for t in tool_list)

    # 3. Unregister tool
    unregistered = local_registry.unregister("custom_test_tool")
    assert unregistered is not None
    assert local_registry.get("custom_test_tool") is None

def test_registry_retrieval():
    # Global tool registry should contain all 5 registered REAL tools
    text_tool = tool_registry.get("TextEntityExtractor")
    ocr_tool = tool_registry.get("OCRTool")
    metadata_tool = tool_registry.get("MetadataExtractor")
    search_tool = tool_registry.get("EvidenceSearchTool")
    timeline_tool = tool_registry.get("TimelineExtractor")

    assert text_tool is not None
    assert ocr_tool is not None
    assert metadata_tool is not None
    assert search_tool is not None
    assert timeline_tool is not None

def test_capability_matching_and_querying():
    # "What capability can perform OCR on this image?"
    ocr_matches = tool_registry.find_by_capability("ocr", input_type="IMAGE")
    assert len(ocr_matches) >= 1
    assert any(t.name == "OCRTool" for t in ocr_matches)

    # Search for entity extraction capability
    entity_matches = tool_registry.find_by_capability("entity_extraction")
    assert len(entity_matches) >= 1
    assert any(t.name == "TextEntityExtractor" for t in entity_matches)

    # Search for metadata capability
    metadata_matches = tool_registry.find_by_capability("metadata_extraction", input_type="IMAGE")
    assert len(metadata_matches) >= 1
    assert any(t.name == "MetadataExtractor" for t in metadata_matches)

    # Search for search capability
    search_matches = tool_registry.find_by_capability("evidence_search")
    assert len(search_matches) >= 1
    assert any(t.name == "EvidenceSearchTool" for t in search_matches)

    # Search for timeline capability
    timeline_matches = tool_registry.find_by_capability("timeline_extraction")
    assert len(timeline_matches) >= 1
    assert any(t.name == "TimelineExtractor" for t in timeline_matches)

@pytest.mark.asyncio
async def test_text_entity_extractor_standardized_output():
    text_tool = tool_registry.get("TextEntityExtractor")
    assert text_tool is not None

    sample_input = ToolInputSchema(
        case_id="CASE-REG-001",
        evidence_id="EVID-REG-001",
        text_content="Suspect @CyberHawk contacted +1-555-0199 and sent funds to 0x71C7656EC7ab88b098defB751B7401B5f6d8976F on 2026-08-10."
    )

    output = await text_tool.execute(sample_input)
    assert output.success is True
    assert output.findings_extracted >= 3
    assert len(output.findings) >= 3

    # Check standardized fields on every finding
    for f in output.findings:
        assert isinstance(f, StandardizedFinding)
        assert f.finding_id is not None
        assert f.case_id == "CASE-REG-001"
        assert f.evidence_id == "EVID-REG-001"
        assert f.finding_type == "ENTITY"
        assert f.entity_type in ("HANDLE", "PHONE", "EMAIL", "IP_ADDRESS", "CRYPTO_WALLET", "TIMESTAMP")
        assert f.entity is not None
        assert f.attribute is not None
        assert f.value is not None
        assert 0.0 <= f.confidence <= 1.0
        assert f.source_tool == "TextEntityExtractor"
        assert isinstance(f.supporting_evidence, dict)
        assert f.timestamp is not None

@pytest.mark.asyncio
async def test_ocr_tool_standardized_output():
    ocr_tool = tool_registry.get("OCRTool")
    assert ocr_tool is not None

    sample_input = ToolInputSchema(
        case_id="CASE-REG-002",
        evidence_id="EVID-REG-002",
        file_path="mock_chat_screenshot.png",
        parameters={"synthetic_ocr_text": "CONFIDENTIAL CHAT LOG: @CyberHawk: Meet at location 37.7749, -122.4194"}
    )

    output = await ocr_tool.execute(sample_input)
    assert output.success is True
    assert output.findings_extracted == 1
    
    finding = output.findings[0]
    assert finding.case_id == "CASE-REG-002"
    assert finding.evidence_id == "EVID-REG-002"
    assert finding.finding_type == "OCR_TEXT"
    assert finding.entity_type == "TEXT"
    assert "CONFIDENTIAL CHAT LOG" in finding.value
    assert finding.source_tool == "OCRTool"

@pytest.mark.asyncio
async def test_metadata_extractor_standardized_output():
    metadata_tool = tool_registry.get("MetadataExtractor")
    assert metadata_tool is not None

    sample_input = ToolInputSchema(
        case_id="CASE-REG-003",
        evidence_id="EVID-REG-003",
        file_path="sample_photo.jpg",
        parameters={
            "synthetic_exif": {
                "gps_coordinates": {"latitude": 37.7749, "longitude": -122.4194},
                "device_model": "Samsung Galaxy S22",
                "datetime_original": "2026-08-12 14:30:00"
            }
        }
    )

    output = await metadata_tool.execute(sample_input)
    assert output.success is True
    assert output.findings_extracted == 3

    gps_finding = next((f for f in output.findings if f.finding_type == "GPS"), None)
    assert gps_finding is not None
    assert gps_finding.entity_type == "LOCATION"
    assert gps_finding.value == {"latitude": 37.7749, "longitude": -122.4194}
    assert gps_finding.source_tool == "MetadataExtractor"

@pytest.mark.asyncio
async def test_evidence_search_tool_standardized_output():
    search_tool = tool_registry.get("EvidenceSearchTool")
    assert search_tool is not None

    sample_input = ToolInputSchema(
        case_id="CASE-REG-004",
        query="cyber crime suspect handles and cell locations",
        text_content="Evidence excerpt mentioning suspect activity and cell tower connections."
    )

    output = await search_tool.execute(sample_input)
    assert output.success is True
    assert len(output.findings) >= 1

    finding = output.findings[0]
    assert finding.finding_type == "SEARCH_RESULT"
    assert finding.entity_type == "KEYWORD"
    assert finding.source_tool == "EvidenceSearchTool"

@pytest.mark.asyncio
async def test_timeline_extractor_standardized_output():
    timeline_tool = tool_registry.get("TimelineExtractor")
    assert timeline_tool is not None

    sample_input = ToolInputSchema(
        case_id="CASE-REG-005",
        evidence_id="EVID-REG-005",
        text_content="Initial contact made on 2026-08-01. Follow-up meeting scheduled on 2026-08-05T15:30:00Z."
    )

    output = await timeline_tool.execute(sample_input)
    assert output.success is True
    assert len(output.findings) >= 2

    for f in output.findings:
        assert f.finding_type == "TIMELINE_EVENT"
        assert f.entity_type == "DATETIME"
        assert f.source_tool == "TimelineExtractor"
