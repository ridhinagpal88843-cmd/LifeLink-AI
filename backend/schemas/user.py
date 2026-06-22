from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from backend.schemas.emergency_health_profile import EmergencyHealthProfileCreate, EmergencyHealthProfileResponse
from backend.schemas.emergency_contact import EmergencyContactCreate, EmergencyContactResponse
from backend.schemas.doctor import DoctorCreate


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["john.doe@gmail.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    phone: str = Field(..., min_length=5, max_length=30, examples=["+1-555-0100"])


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, examples=["securepassword123"])
    
    # Nested registration structures
    emergency_health_profile: EmergencyHealthProfileCreate
    primary_doctor: Optional[DoctorCreate] = None
    
    # Enforces a maximum of 5 emergency contacts during signup
    emergency_contacts: List[EmergencyContactCreate] = Field(
        default=[],
        max_items=5,
        description="List of up to 5 emergency contacts"
    )


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Nested response structures
    emergency_health_profile: Optional[EmergencyHealthProfileResponse] = None
    emergency_contacts: List[EmergencyContactResponse] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=5, max_length=30)
    
    # Updates to nested resources
    emergency_health_profile: Optional[EmergencyHealthProfileCreate] = None
    primary_doctor: Optional[DoctorCreate] = None
    emergency_contacts: Optional[List[EmergencyContactCreate]] = Field(None, max_items=5)
