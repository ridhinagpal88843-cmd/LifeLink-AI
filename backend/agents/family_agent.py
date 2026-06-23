import logging
from typing import Dict, Any, List, Optional
from backend.mcp.client import MCPClientRegistry
from backend.services.voice_service import VoiceCallEngine

logger = logging.getLogger(__name__)


class FamilyCommunicationAgent:
    """
    Agent responsible for calling emergency contacts, utilizing Voice Call MCP Tool.
    """

    def __init__(self, mcp_client: Optional[MCPClientRegistry] = None):
        self.mcp_client = mcp_client
        self.voice_engine = VoiceCallEngine()

    async def alert_family_contacts(self, contacts: List[Dict[str, Any]], patient_name: str, 
                                    incident_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Loops through contacts and triggers outbound calls concurrently.
        """
        if not contacts:
            logger.info("Outbound family alerts skipped: No contacts registered.")
            return []

        # Sort contacts by priority ranking (1 is highest)
        sorted_contacts = sorted(contacts, key=lambda c: c.get("priority", 5))
        
        calls = []
        for contact in sorted_contacts:
            phone = contact.get("phone")
            if not phone:
                continue

            script = self.voice_engine.generate_contact_script(
                patient_name=patient_name,
                relationship=contact.get("relationship", "Family Member"),
                emergency_type=incident_details.get("emergency_type", "Telemetry Alert"),
                location=incident_details.get("location", "Patient Coordinates"),
                assigned_hospital=incident_details.get("assigned_hospital", "Local Hospital"),
                eta=incident_details.get("eta_minutes", 7)
            )

            # Trigger call via Voice Call MCP
            if self.mcp_client:
                response = self.mcp_client.voice_place_call(phone=phone, script_text=script)
            else:
                response = self.voice_engine.trigger_outbound_call(to_phone=phone, script_text=script)
                
            calls.append(response)
            
        logger.info(f"Family Communication Agent successfully queued {len(calls)} calls.")
        return calls
