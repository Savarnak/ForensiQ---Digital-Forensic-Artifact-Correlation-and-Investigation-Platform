from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class InvestigationGoalCreate(BaseModel):
    goal_text: str = Field(..., json_schema_extra={"example": "Identify primary suspect handles, cross-reference geotags, and reconstruct timeline."})
    priority: Optional[str] = Field("MEDIUM", json_schema_extra={"example": "HIGH"})

class InvestigationGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    goal_text: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
