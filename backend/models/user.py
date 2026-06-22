import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    """
    SQLAlchemy model representing a registered User in LifeLink AI.
    """
    __tablename__ = "users"

    # UUID primary key represented as 36-character string
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    is_active = Column(Boolean, default=True)

    # Auditing Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    # One-to-One relationship: A user has exactly one Emergency Health Profile
    emergency_health_profile = relationship(
        "EmergencyHealthProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # One-to-Many relationship: A user has up to 5 Emergency Contacts
    emergency_contacts = relationship(
        "EmergencyContact",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined"
    )
