from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class TaskStep(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    tool_name: str
    objective: str
    evidence_id: Optional[str] = None
    file_name: Optional[str] = None
    status: str = "PENDING"  # PENDING, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None

class CaseState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    case_number: str
    run_id: str = ""
    investigation_goal: str
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[TaskStep] = Field(default_factory=list)
    raw_findings: List[Dict[str, Any]] = Field(default_factory=list)
    standardized_findings: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_graph_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_graph_edges: List[Dict[str, Any]] = Field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_leads: List[Dict[str, Any]] = Field(default_factory=list)
    execution_logs: List[str] = Field(default_factory=list)
    audit_events: List[Dict[str, Any]] = Field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 2
    needs_additional_investigation: bool = False
    investigation_summary: str = ""
    error: Optional[str] = None
