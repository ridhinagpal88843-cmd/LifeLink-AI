import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class VoiceCallEngine:
    """
    Service responsible for generating dynamic text-to-speech voice scripts 
    and integrating with Voice Call APIs (Twilio, Exotel) via MCP tools.
    """

    @staticmethod
    def generate_doctor_script(patient_name: str, emergency_type: str, severity: str, 
                               location: str, medical_conditions: str, allergies: str, 
                               assigned_hospital: str, eta: int) -> str:
        """
        Generates a clinically-focused voice script for the patient's primary care physician.
        """
        conditions_str = medical_conditions if medical_conditions else "no documented chronic conditions"
        allergies_str = allergies if allergies else "no documented allergies"
        hospital_str = assigned_hospital if assigned_hospital else "the local emergency department"

        script = (
            f"Hello, this is an automated dispatch from LifeLink AI. "
            f"Your patient, {patient_name}, is experiencing a medical emergency classified as {emergency_type} "
            f"with a severity rating of {severity}. "
            f"Patient is currently located at {location}. "
            f"Patient medical records indicate the following conditions: {conditions_str}. "
            f"Allergies on file: {allergies_str}. "
            f"An ambulance has been dispatched and the patient is being transported to {hospital_str} "
            f"with an estimated arrival in {eta} minutes. "
            f"Please stand by for updates or contact the triage department at {hospital_str}."
        )
        return script

    @staticmethod
    def generate_contact_script(patient_name: str, relationship: str, emergency_type: str, 
                                location: str, assigned_hospital: str, eta: int) -> str:
        """
        Generates a reassuring, action-oriented voice script for the patient's emergency contact family members.
        """
        hospital_str = assigned_hospital if assigned_hospital else "the local hospital"
        
        script = (
            f"Hello, this is an urgent notification from LifeLink AI for the emergency contact of {patient_name}. "
            f"We are calling to inform you that {patient_name} has triggered a medical alert for {emergency_type}. "
            f"An emergency response team has responded and is providing care. "
            f"{patient_name} is being transported to {hospital_str}. "
            f"The ambulance is estimated to arrive at the hospital in {eta} minutes. "
            f"You can monitor real-time updates and location coordinates via the LifeLink mobile link sent to your phone. "
            f"Please head to {hospital_str} or contact emergency services."
        )
        return script

    def trigger_outbound_call(self, to_phone: str, script_text: str, provider: str = "twilio") -> Dict[str, Any]:
        """
        Triggers an outbound call using the chosen provider (Twilio or Exotel) TwiML/voice payload.
        In production, this translates to an HTTP request to the provider's API.
        """
        logger.info(f"Triggering outbound voice call to {to_phone} using {provider}...")
        logger.debug(f"Voice Script Payload: '{script_text}'")

        # Mocking the outbound API payload
        # Under Twilio:
        # client.calls.create(to=to_phone, from_=settings.TWILIO_PHONE, twiml=f"<Response><Say>{script_text}</Say></Response>")
        
        mock_response = {
            "status": "queued",
            "call_sid": f"CA{hash(to_phone + script_text) & 0xffffffffffff}",
            "provider": provider,
            "recipient": to_phone,
            "script_length": len(script_text)
        }
        return mock_response
