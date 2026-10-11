from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class InvestigationTask(Base):
    __tablename__ = "investigation_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_run_id = Column(String(36), ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, COMPLETED, FAILED
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    investigation_run = relationship("InvestigationRun", back_populates="tasks")
