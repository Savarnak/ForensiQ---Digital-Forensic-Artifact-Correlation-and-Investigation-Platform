from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Type, Any, List, Optional, Union
from datetime import datetime
import uuid
from app.core.logging import logger

class StandardizedFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    evidence_id: Optional[str] = None
    finding_type: str  # e.g. ENTITY, GPS, OCR_TEXT, TIMELINE_EVENT, METADATA, SEARCH_RESULT
    entity_type: Optional[str] = None  # e.g. HANDLE, PHONE, EMAIL, LOCATION, DEVICE, DATETIME, KEYWORD
    entity: Optional[str] = None  # Human-readable entity string e.g. "@CyberHawk", "Samsung Galaxy S22"
    attribute: Optional[str] = None  # Property key e.g. "username", "gps_coordinates", "event_summary"
    value: Any = None  # Raw extracted value or dict
    confidence: float = 1.0
    source_tool: str
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ToolInputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    evidence_id: Optional[str] = None
    file_path: Optional[str] = None
    text_content: Optional[str] = None
    query: Optional[str] = None
    input_type: Optional[str] = None  # e.g. TEXT, IMAGE, CHAT_LOG, DOCUMENT
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ToolOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    success: bool
    findings_extracted: int
    data: Dict[str, Any] = Field(default_factory=dict)
    findings: List[StandardizedFinding] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

class BaseInvestigativeTool(ABC):
    name: str = "base_tool"
    description: str = "Base investigative capability/tool interface"
    supported_input_types: List[str] = ["TEXT", "IMAGE", "CHAT_LOG", "DOCUMENT", "FILE"]
    capabilities: List[str] = []
    input_schema: Type[BaseModel] = ToolInputSchema
    output_schema: Type[BaseModel] = ToolOutputSchema

    @abstractmethod
    async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        """Executes the tool capability on given input data and returns standardized findings."""
        pass

    async def run(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        """Alias for execute() to ensure backward compatibility."""
        return await self.execute(input_data)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseInvestigativeTool] = {}

    def register(self, tool: Union[BaseInvestigativeTool, Type[BaseInvestigativeTool]]) -> BaseInvestigativeTool:
        """Registers a tool instance or tool class."""
        if isinstance(tool, type) and issubclass(tool, BaseInvestigativeTool):
            instance = tool()
        elif isinstance(tool, BaseInvestigativeTool):
            instance = tool
        else:
            raise TypeError("tool must be an instance or subclass of BaseInvestigativeTool")

        if instance.name in self._tools:
            logger.warning(f"Overwriting existing tool registration: '{instance.name}'")
        
        self._tools[instance.name] = instance
        logger.info(f"Registered investigative capability: '{instance.name}' (Capabilities: {instance.capabilities})")
        return instance

    def unregister(self, name: str) -> Optional[BaseInvestigativeTool]:
        """Removes a tool from the registry by name."""
        tool = self._tools.pop(name, None)
        if tool:
            logger.info(f"Unregistered tool capability: '{name}'")
        return tool

    def get(self, name: str) -> Optional[BaseInvestigativeTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def get_tool(self, name: str) -> Optional[BaseInvestigativeTool]:
        """Alias for get() to ensure backward compatibility."""
        return self.get(name)

    def list(self) -> List[Dict[str, Any]]:
        """Returns metadata specifications for all registered capabilities."""
        tool_specs = []
        for name, tool in self._tools.items():
            schema_dict = {}
            if hasattr(tool.input_schema, "model_json_schema"):
                schema_dict = tool.input_schema.model_json_schema()
            elif hasattr(tool.input_schema, "schema"):
                schema_dict = tool.input_schema.schema()

            tool_specs.append({
                "name": tool.name,
                "description": tool.description,
                "supported_input_types": getattr(tool, "supported_input_types", []),
                "capabilities": tool.capabilities,
                "input_schema": schema_dict
            })
        return tool_specs

    def list_tools(self) -> List[Dict[str, Any]]:
        """Alias for list() to ensure backward compatibility."""
        return self.list()

    def find_by_capability(self, capability: str, input_type: Optional[str] = None) -> List[BaseInvestigativeTool]:
        """
        Finds all tools matching a capability (case-insensitive substring or tag match)
        and optionally filtering by supported input type.
        """
        cap_query = capability.lower().strip()
        matching_tools: List[BaseInvestigativeTool] = []

        for name, tool in self._tools.items():
            # Check capability match (exact tag match, or substring match in name/description/capabilities)
            cap_match = any(cap_query in cap.lower() for cap in tool.capabilities) or \
                        cap_query in tool.name.lower() or \
                        cap_query in tool.description.lower()

            if cap_match:
                if input_type:
                    supported = getattr(tool, "supported_input_types", [])
                    if any(input_type.upper() == st.upper() for st in supported):
                        matching_tools.append(tool)
                else:
                    matching_tools.append(tool)

        return matching_tools

# Alias AgentRegistry to ToolRegistry for full conceptual alignment
AgentRegistry = ToolRegistry

# Global Registry instance
tool_registry = ToolRegistry()
agent_registry = tool_registry

def register_tool():
    """Decorator to register a tool class into the global tool registry."""
    def decorator(cls: Type[BaseInvestigativeTool]):
        tool_registry.register(cls)
        return cls
    return decorator
