from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class CaseCreate(BaseModel):
    case_number: str = Field(..., json_schema_extra={"example": "CASE-2026-0891"})
    title: str = Field(..., json_schema_extra={"example": "Operation Cygnus - Coordinated Online Grooming Network"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Multi-platform digital evidence analysis case"})

class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
