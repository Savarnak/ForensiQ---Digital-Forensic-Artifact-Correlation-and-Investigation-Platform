from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class InvestigationRunCreate(BaseModel):
    goal_id: Optional[str] = Field(None, json_schema_extra={"example": "goal-uuid-1234"})

class InvestigationTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_run_id: str
    case_id: str
    tool_name: str
    objective: str
    status: str
    result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class InvestigationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    goal_id: Optional[str]
    status: str
    summary: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    tasks: List[InvestigationTaskResponse] = []
