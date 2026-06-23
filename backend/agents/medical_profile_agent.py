from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.mcp.client import MCPClientRegistry


class MedicalProfileAgent:
    """
    Agent responsible for loading, validating, and formatting patient medical histories
    and contacts, utilizing the Patient Database MCP Tool with local DB queries as fallback.
    """

    def __init__(self, db: Session, mcp_client: Optional[MCPClientRegistry] = None):
        self.db = db
        self.mcp_client = mcp_client or MCPClientRegistry(db)

    def retrieve_patient_history(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user registration and clinical history from Patient Database MCP.
        """
        # Call the MCP Patient DB Tool
        mcp_res = self.mcp_client.patient_db_fetch_profile(user_id)
        
        # If success or fallback, return formatting
        patient = mcp_res["patient"]
        
        # Format the emergency contacts and doctor nested fields
        # Re-query DB locally to resolve relationships if not populated by MCP tool payload
        from backend.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        return {
            "patient_info": {
                "id": patient["id"],
                "full_name": patient["name"],
                "phone": patient["phone"],
                "email": patient["email"]
            },
            "clinical_info": {
                "blood_group": patient["blood_group"],
                "medical_conditions": patient["conditions"] or "",
                "allergies": patient["allergies"] or "",
                "current_medications": patient["medications"] or "",
                "emergency_preferences": patient["preferences"] or ""
            },
            "primary_doctor": {
                "name": user.emergency_health_profile.primary_doctor.name if user.emergency_health_profile.primary_doctor else None,
                "phone": user.emergency_health_profile.primary_doctor.phone if user.emergency_health_profile.primary_doctor else None,
                "email": user.emergency_health_profile.primary_doctor.email if user.emergency_health_profile.primary_doctor else None,
                "specialty": user.emergency_health_profile.primary_doctor.specialty if user.emergency_health_profile.primary_doctor else None
            } if user.emergency_health_profile.primary_doctor else None,
            "emergency_contacts": [
                {
                    "name": contact.name,
                    "relationship": contact.relationship,
                    "phone": contact.phone,
                    "priority": contact.priority
                } for contact in user.emergency_contacts
            ]
        }
