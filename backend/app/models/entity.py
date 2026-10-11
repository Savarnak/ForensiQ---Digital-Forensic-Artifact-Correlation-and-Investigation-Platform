from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False) # e.g. PERSON, HANDLE, DEVICE, LOCATION, EMAIL, PHONE
    name = Column(String(255), nullable=False)
    identifier = Column(String(255), nullable=True) # Unique key e.g. @CyberHawk or +15550199
    properties = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="entities")
    outgoing_relationships = relationship("Relationship", foreign_keys="[Relationship.source_entity_id]", back_populates="source_entity", cascade="all, delete-orphan")
    incoming_relationships = relationship("Relationship", foreign_keys="[Relationship.target_entity_id]", back_populates="target_entity", cascade="all, delete-orphan")
