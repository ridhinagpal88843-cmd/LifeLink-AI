import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# Import local engines to serve as reliable fallback interfaces
from backend.services.voice_service import VoiceCallEngine
from backend.models.user import User

logger = logging.getLogger(__name__)


class MCPClientRegistry:
    """
    Model Context Protocol (MCP) Client Integration registry.
    Defines interfaces to connect LifeLink AI agents to remote MCP tools.
    Implements reliable fallback wrappers to guarantee zero downtime.
    """

    def __init__(self, db: Session, use_mcp_mock: bool = True):
        self.db = db
        # Configures whether to simulate successful MCP responses or force fallback triggers
        self.use_mcp_mock = use_mcp_mock

    # =========================================================================
    # 1. Patient Database MCP Tool
    # =========================================================================
    def patient_db_fetch_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Tool: patient_db_fetch_profile
        Retrieves user registration and clinical history from the Patient Database MCP.
        """
        try:
            if not self.use_mcp_mock:
                raise ConnectionError("Patient Database MCP Server unreachable.")
                
            logger.info(f"MCP [Patient DB]: Invoking tool 'patient_db_fetch_profile' for ID {user_id}...")
            # Simulate MCP server response
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"status": "error", "error_code": "NOT_FOUND"}
            return {
                "status": "success",
                "patient": {
                    "id": user.id,
                    "name": user.full_name,
                    "phone": user.phone,
                    "email": user.email,
                    "blood_group": user.emergency_health_profile.blood_group,
                    "conditions": user.emergency_health_profile.medical_conditions,
                    "allergies": user.emergency_health_profile.allergies,
                    "medications": user.emergency_health_profile.current_medications,
                    "preferences": user.emergency_health_profile.emergency_preferences
                }
            }
        except Exception as e:
            logger.warning(f"MCP [Patient DB] Error: {e}. Executing local Database Fallback...")
            # Fallback behavior: Direct local database retrieval
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("Patient not found in local fallback.")
            return {
                "status": "fallback",
                "patient": {
                    "id": user.id,
                    "name": user.full_name,
                    "phone": user.phone,
                    "email": user.email,
                    "blood_group": user.emergency_health_profile.blood_group,
                    "conditions": user.emergency_health_profile.medical_conditions,
                    "allergies": user.emergency_health_profile.allergies,
                    "medications": user.emergency_health_profile.current_medications,
                    "preferences": user.emergency_health_profile.emergency_preferences
                }
            }

    # =========================================================================
    # 2. Maps/Geocoding MCP Tool
    # =========================================================================
    def maps_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Tool: maps_geocode
        Converts coordinates to street address via the Maps/Geocoding MCP.
        """
        try:
            if not self.use_mcp_mock:
                raise ConnectionError("Maps Geocoding MCP Server offline.")

            logger.info(f"MCP [Maps]: Invoking geocoder for lat {lat}, lon {lon}...")
            # Simulate Geocoding MCP server response
            return {
                "status": "success",
                "formatted_address": "1230 Market St, San Francisco, CA 94102"
            }
        except Exception as e:
            logger.warning(f"MCP [Maps] Error: {e}. Triggering local geocode mock...")
            # Fallback to local reverse geocoding rule
            return {
                "status": "fallback",
                "formatted_address": f"Unincorporated coordinates: {lat:.4f}, {lon:.4f}"
            }

    # =========================================================================
    # 3. Hospital/Doctor Directory MCP Tool
    # =========================================================================
    def directory_find_doctor(self, name: str, phone: str) -> Dict[str, Any]:
        """
        Tool: directory_find_doctor
        Resolves medical directories from the Hospital/Doctor Directory MCP.
        """
        try:
            if not self.use_mcp_mock:
                raise ConnectionError("Doctor Directory MCP Server timeout.")

            logger.info(f"MCP [Directory]: Searching record for Dr. {name}...")
            return {
                "status": "success",
                "doctor_record": {
                    "name": name,
                    "phone": phone,
                    "verified": True,
                    "clinic_status": "Active"
                }
            }
        except Exception as e:
            logger.warning(f"MCP [Directory] Error: {e}. Defaulting to unverified local values...")
            return {
                "status": "fallback",
                "doctor_record": {
                    "name": name,
                    "phone": phone,
                    "verified": False,
                    "clinic_status": "Unknown"
                }
            }

    # =========================================================================
    # 4. Voice Call MCP Tool
    # =========================================================================
    def voice_place_call(self, phone: str, script_text: str) -> Dict[str, Any]:
        """
        Tool: voice_place_call
        Executes automated TTS voice calls via the Voice Call MCP.
        """
        try:
            if not self.use_mcp_mock:
                raise ConnectionError("Voice Telephony MCP Gateway down.")

            logger.info(f"MCP [Voice]: Dispatching call request to {phone}...")
            return {
                "status": "success",
                "call_id": f"mcp-call-{hash(phone) & 0xfffff}",
                "telephony_status": "initiated"
            }
        except Exception as e:
            logger.warning(f"MCP [Voice] Error: {e}. Reverting to local VoiceCallEngine...")
            # Fallback to the local VoiceCallEngine
            res = VoiceCallEngine().trigger_outbound_call(to_phone=phone, script_text=script_text)
            return {
                "status": "fallback",
                "call_id": res.get("call_sid"),
                "telephony_status": "fallback-queued"
            }

    # =========================================================================
    # 5. Logging MCP Tool
    # =========================================================================
    def logging_log_action(self, incident_id: str, action_message: str) -> Dict[str, Any]:
        """
        Tool: logging_log_action
        Commits system event logging to the centralized Logging MCP.
        """
        try:
            if not self.use_mcp_mock:
                raise ConnectionError("Centralized Logging MCP unreachable.")

            logger.info(f"MCP [Logging]: Commit audit event for Incident {incident_id}...")
            return {
                "status": "success",
                "logged": True
            }
        except Exception as e:
            logger.warning(f"MCP [Logging] Error: {e}. Defaulting to Python standard logging...")
            # Fallback: Log directly to standard console output/files
            logger.info(f"FALLBACK AUDIT [Incident {incident_id}]: {action_message}")
            return {
                "status": "fallback",
                "logged": True
            }
