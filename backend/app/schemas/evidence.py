from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    file_name: str
    file_path: str
    file_type: str
    mime_type: Optional[str]
    hash_sha256: Optional[str]
    file_size_bytes: Optional[str]
    uploaded_at: datetime
    extracted_metadata: Dict[str, Any]
