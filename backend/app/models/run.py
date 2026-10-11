from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class InvestigationRun(Base):
    __tablename__ = "investigation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey("investigation_goals.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, RUNNING, COMPLETED, FAILED
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="investigation_runs")
    goal = relationship("InvestigationGoal", back_populates="investigation_runs")
    tasks = relationship("InvestigationTask", back_populates="investigation_run", cascade="all, delete-orphan")
