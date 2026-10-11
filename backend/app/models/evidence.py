from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False) # e.g. IMAGE, CHAT_LOG, AUDIO, DOCUMENT
    mime_type = Column(String(100), nullable=True)
    hash_sha256 = Column(String(64), nullable=True)
    file_size_bytes = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extracted_metadata = Column(JSON, default=dict, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="evidence_items")
    findings = relationship("Finding", back_populates="evidence", cascade="all, delete-orphan")
