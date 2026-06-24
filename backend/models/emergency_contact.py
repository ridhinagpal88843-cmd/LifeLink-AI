import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship as orm_relationship

from backend.database import Base


class EmergencyContact(Base):
    """
    SQLAlchemy model representing a contact called during an emergency event.
    Each user can configure up to 5 contacts, ranked by priority (1 to 5).
    """
    __tablename__ = "emergency_contacts"

    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)
    phone = Column(String(30), nullable=False)
    priority = Column(Integer, nullable=False)  # 1 to 5

    # Auditing Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    # Relationships
    user = orm_relationship("User", back_populates="emergency_contacts")
