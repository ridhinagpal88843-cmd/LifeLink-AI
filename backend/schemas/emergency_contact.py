from datetime import datetime
from pydantic import BaseModel, Field


class EmergencyContactBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Sarah Doe"])
    relationship: str = Field(..., min_length=2, max_length=50, examples=["Spouse"])
    phone: str = Field(..., min_length=5, max_length=30, examples=["+1-555-0188"])
    priority: int = Field(..., ge=1, le=5, description="Contact priority level, where 1 is highest priority", examples=[1])


class EmergencyContactCreate(EmergencyContactBase):
    pass


class EmergencyContactResponse(EmergencyContactBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
