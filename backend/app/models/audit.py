from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False) # e.g. CASE_CREATED, EVIDENCE_UPLOADED, GOAL_ADDED, INVESTIGATION_STARTED
    actor = Column(String(100), nullable=False) # e.g. INVESTIGATOR, ARGUS_SYSTEM
    details = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="audit_events")

# Alias for backwards compatibility
AuditLog = AuditEvent
