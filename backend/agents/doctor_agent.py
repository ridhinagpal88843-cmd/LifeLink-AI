import logging
from typing import Dict, Any, Optional
from backend.mcp.client import MCPClientRegistry
from backend.services.voice_service import VoiceCallEngine

logger = logging.getLogger(__name__)


class DoctorCommunicationAgent:
    """
    Agent responsible for preparing clinical alert scripts and triggering calls
    to family doctors, utilizing Doctor Directory and Voice Call MCP Tools.
    """

    def __init__(self, mcp_client: Optional[MCPClientRegistry] = None):
        self.mcp_client = mcp_client
        self.voice_engine = VoiceCallEngine()

    async def alert_family_doctor(self, doctor_info: Dict[str, Any], patient_name: str, 
                                  incident_details: Dict[str, Any], medical_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries doctor status and initiates outbound telephony voice call.
        """
        doctor_name = doctor_info.get("name", "Physician")
        doctor_phone = doctor_info.get("phone")
        if not doctor_phone:
            logger.info("Outbound doctor alert skipped: No physician phone number provided.")
            return {"status": "skipped", "recipient": None}

        # 1. Resolve Doctor Directory status using MCP
        if self.mcp_client:
            dir_res = self.mcp_client.directory_find_doctor(doctor_name, doctor_phone)
            logger.info(f"MCP [Directory] Verification status: {dir_res.get('doctor_record', {}).get('clinic_status')}")

        # 2. Generate the voice script
        script = self.voice_engine.generate_doctor_script(
            patient_name=patient_name,
            emergency_type=incident_details.get("emergency_type", "Telemetry Alert"),
            severity=incident_details.get("severity", "Critical"),
            location=incident_details.get("location", "Patient Coordinates"),
            medical_conditions=medical_history.get("medical_conditions", ""),
            allergies=medical_history.get("allergies", ""),
            assigned_hospital=incident_details.get("assigned_hospital", "Local Hospital"),
            eta=incident_details.get("eta_minutes", 7)
        )

        # 3. Trigger Voice call via Voice MCP
        if self.mcp_client:
            response = self.mcp_client.voice_place_call(phone=doctor_phone, script_text=script)
        else:
            response = self.voice_engine.trigger_outbound_call(to_phone=doctor_phone, script_text=script)

        return response
