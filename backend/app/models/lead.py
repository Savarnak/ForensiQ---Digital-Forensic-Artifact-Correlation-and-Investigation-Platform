from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

LEAD_DISCLAIMER_TEXT = "Investigative aid provided for officer/analyst review. Does not constitute a determination of guilt or administrative finding."

class LeadStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_MORE_ANALYSIS = "NEEDS_MORE_ANALYSIS"
    # Backwards compatibility aliases
    PROPOSED = "PENDING_REVIEW"
    INVESTIGATOR_APPROVED = "APPROVED"
    INVESTIGATOR_REJECTED = "REJECTED"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    priority = Column(String(20), default="MEDIUM", nullable=False)
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING_REVIEW, nullable=False)
    confidence = Column(Float, default=0.85, nullable=False)
    supporting_evidence_ids = Column(JSON, default=list, nullable=False)
    supporting_findings = Column(JSON, default=list, nullable=False)
    reasoning_factors = Column(JSON, default=list, nullable=False)
    reasoning_chain = Column(JSON, default=list, nullable=False)
    next_recommended_actions = Column(JSON, default=list, nullable=False)
    disclaimer = Column(Text, default=LEAD_DISCLAIMER_TEXT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="leads")
