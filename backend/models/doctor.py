import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Doctor(Base):
    """
    SQLAlchemy model representing a primary care physician in LifeLink AI.
    Allows multiple users/profiles to refer to the same doctor.
    """
    __tablename__ = "doctors"

    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(100), nullable=True)
    specialty = Column(String(100), nullable=True)

    # Auditing Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    # One-to-Many relationship back to patient health profiles
    patients = relationship("EmergencyHealthProfile", back_populates="primary_doctor")
