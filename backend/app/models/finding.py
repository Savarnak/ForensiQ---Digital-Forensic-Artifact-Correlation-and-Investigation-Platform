from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False)
    finding_type = Column(String(50), nullable=False) # e.g. ENTITY, GPS, OCR_TEXT, TIMELINE_EVENT
    content = Column(JSON, nullable=False) # The structured data extracted
    confidence = Column(Float, default=1.0, nullable=False)
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    provenance = Column(JSON, default=dict, nullable=False) # Provenance trace dictionary

    # Relationships
    case = relationship("Case", back_populates="findings")
    evidence = relationship("Evidence", back_populates="findings")
