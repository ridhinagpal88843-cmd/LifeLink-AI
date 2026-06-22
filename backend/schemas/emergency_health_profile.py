from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.schemas.doctor import DoctorResponse


class EmergencyHealthProfileBase(BaseModel):
    blood_group: Optional[str] = Field(None, max_length=10, description="Blood group (e.g. O+, A-)", examples=["O+"])
    medical_conditions: Optional[str] = Field(None, description="Existing chronic illnesses or medical conditions", examples=["Hypertension, Asthma"])
    allergies: Optional[str] = Field(None, description="Known drug, food, or chemical allergies", examples=["Penicillin, Peanuts"])
    current_medications: Optional[str] = Field(None, description="List of medications currently being taken", examples=["Lisinopril 10mg daily"])
    emergency_preferences: Optional[str] = Field(None, description="Custom instruction details during critical response", examples=["DNR active, preferred clinic: St. Jude Hospital"])


class EmergencyHealthProfileCreate(EmergencyHealthProfileBase):
    pass


class EmergencyHealthProfileResponse(EmergencyHealthProfileBase):
    id: str
    user_id: str
    primary_doctor_id: Optional[str] = None
    primary_doctor: Optional[DoctorResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
