"""
Models Layer (SQLAlchemy Declarative Entities)
==============================================

This package exports all database tables/entities.
- User: Personal user data and auth credentials.
- EmergencyHealthProfile: Clinical and vital preferences.
- Doctor: Primary physician registration.
- EmergencyContact: User-specific contacts with priority mappings.
"""

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact

__all__ = ["User", "Doctor", "EmergencyHealthProfile", "EmergencyContact"]
