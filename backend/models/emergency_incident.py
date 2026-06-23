import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer, func
from sqlalchemy.orm import relationship

from backend.database import Base


class EmergencyIncident(Base):
    """
    SQLAlchemy model representing an active or resolved Emergency Incident in LifeLink AI.
    Integrates with audit trails and multi-agent coordination workflows.
    """
    __tablename__ = "emergency_incidents"

    # UUID primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)

    # Core Incident Details
    emergency_type = Column(String(100), nullable=False)  # e.g., "Cardiac Arrest", "Severe Trauma"
    severity = Column(String(50), nullable=False)         # e.g., "Critical", "High", "Moderate", "Low"
    status = Column(String(50), default="Detected", nullable=False)  # e.g., "Detected", "Dispatching", "Resolved"

    # Geolocation coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Immutable Medical Profile Snapshot
    medical_profile_snapshot = Column(Text, nullable=False)

    # Agent Coordination & Dispatch Data
    assigned_hospital = Column(String(100), nullable=True)
    assigned_ambulance = Column(String(50), nullable=True)
    estimated_arrival_minutes = Column(Integer, nullable=True)
    agent_decision_log = Column(Text, nullable=True)      # Triage/Dispatch rationales

    # Auditing Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())

    # Relationships
    user = relationship("User")
    assigned_doctor = relationship("Doctor")
    
    # State transitions ordered chronologically
    state_transitions = relationship(
        "IncidentStateTransition",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentStateTransition.timestamp",
        lazy="joined"
    )


class IncidentStateTransition(Base):
    """
    SQLAlchemy model recording every lifecycle state transition for an incident.
    Ensures a clean audit trail of treatment timelines.
    """
    __tablename__ = "incident_state_transitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    incident_id = Column(String(36), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), nullable=False)
    
    # State values: Detected, Dispatching, Ambulance En Route, Doctor Contacted, Family Contacted, Patient Reached, Hospital Admission, Resolved, Closed
    status = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    # Relationships
    incident = relationship("EmergencyIncident", back_populates="state_transitions")
