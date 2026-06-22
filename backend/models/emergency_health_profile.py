import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class EmergencyHealthProfile(Base):
    """
    SQLAlchemy model representing a patient's Emergency Health Profile.
    Houses critical medical context retrieved during accidents or care operations.
    """
    __tablename__ = "emergency_health_profiles"

    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    primary_doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)

    # Core Medical Fields
    blood_group = Column(String(10), nullable=True)
    medical_conditions = Column(Text, nullable=True)     # comma-separated or descriptive text
    allergies = Column(Text, nullable=True)              # comma-separated or descriptive text
    current_medications = Column(Text, nullable=True)    # comma-separated or descriptive text
    emergency_preferences = Column(Text, nullable=True)  # custom response steps / preferences

    # Auditing Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="emergency_health_profile")
    primary_doctor = relationship("Doctor", back_populates="patients", lazy="joined")
