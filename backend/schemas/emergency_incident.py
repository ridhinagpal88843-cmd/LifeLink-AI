from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EmergencyIncidentBase(BaseModel):
    emergency_type: str = Field(..., min_length=2, max_length=100, description="Type of incident", examples=["Cardiac Arrest"])
    severity: str = Field(..., min_length=2, max_length=50, description="Severity assessment level", examples=["Critical"])
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Geographic latitude coordinate", examples=[37.7749])
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Geographic longitude coordinate", examples=[-122.4194])


class IncidentStateTransitionResponse(BaseModel):
    id: str
    incident_id: str
    status: str
    notes: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class EmergencyIncidentCreate(EmergencyIncidentBase):
    pass


class EmergencyIncidentResponse(EmergencyIncidentBase):
    id: str
    user_id: str
    assigned_doctor_id: Optional[str] = None
    status: str
    medical_profile_snapshot: str  # Serialized JSON string
    assigned_hospital: Optional[str] = None
    assigned_ambulance: Optional[str] = None
    estimated_arrival_minutes: Optional[int] = None
    agent_decision_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    state_transitions: List[IncidentStateTransitionResponse] = []

    class Config:
        from_attributes = True


class EmergencyIncidentUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50, description="e.g. Detected, Dispatching, Ambulance En Route, Doctor Contacted, Family Contacted, Patient Reached, Hospital Admission, Resolved, Closed")
    assigned_hospital: Optional[str] = Field(None, max_length=100)
    assigned_ambulance: Optional[str] = Field(None, max_length=50)
    estimated_arrival_minutes: Optional[int] = Field(None, ge=0)
    agent_decision_log: Optional[str] = Field(None, description="Updates to multi-agent coordinate decisions")
