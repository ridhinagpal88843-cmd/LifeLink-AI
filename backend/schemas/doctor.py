from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Dr. Evelyn Carter"])
    phone: str = Field(..., min_length=5, max_length=30, examples=["+1-555-0199"])
    email: Optional[EmailStr] = Field(None, examples=["evelyn.carter@hospital.org"])
    specialty: Optional[str] = Field(None, max_length=100, examples=["Cardiology"])


class DoctorCreate(DoctorBase):
    pass


class DoctorResponse(DoctorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
