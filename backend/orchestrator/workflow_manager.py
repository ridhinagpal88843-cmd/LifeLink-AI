import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.emergency_incident import EmergencyIncident
from backend.agents.coordinator_agent import EmergencyCoordinatorAgent
from backend.agents.location_agent import LocationRoutingAgent
from backend.agents.audit_agent import AuditAgent

logger = logging.getLogger(__name__)

# Coordinates mapping for hospital coordinates
HOSPITAL_COORDINATES = {
    "Mercy General Hospital": (37.7849, -122.4094),
    "City General Hospital": (37.7650, -122.4400)
}


class EmergencyWorkflowManager:
    """
    Main entry point facade for driving emergency flows.
    Delegates multi-agent tasks to EmergencyCoordinatorAgent and updates active location tracking.
    """

    def __init__(self, db: Session):
        self.db = db
        self.coordinator = EmergencyCoordinatorAgent(db)
        self.location_agent = LocationRoutingAgent()
        self.audit_agent = AuditAgent(db)

    async def trigger_emergency_workflow(self, user_id: str, telemetry_data: Dict[str, Any]) -> EmergencyIncident:
        """
        Triggers the multi-agent emergency coordination flow.
        """
        logger.info(f"Ingesting emergency vitals event for user: {user_id}")
        incident = await self.coordinator.orchestrate_emergency(user_id, telemetry_data)
        return incident

    async def update_incident_location(self, incident_id: str, latitude: float, longitude: float) -> EmergencyIncident:
        """
        Allows ambulance telemetry to update the patient's current active location,
        re-evaluating distances, travel duration (ETA), and logging audit logs.
        """
        incident = self.db.query(EmergencyIncident).filter(EmergencyIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found.")

        incident.latitude = latitude
        incident.longitude = longitude

        # Re-geocode updated coordinate
        geocode_res = self.location_agent.reverse_geocode(latitude, longitude)
        new_address = geocode_res.address

        # Re-calculate routing distance/ETA to assigned hospital
        hospital_name = incident.assigned_hospital or "Mercy General Hospital"
        h_lat, h_lon = HOSPITAL_COORDINATES.get(hospital_name, (37.7849, -122.4094))
        
        routing_res = self.location_agent.calculate_routing(
            from_lat=latitude,
            from_lon=longitude,
            hospital_name=hospital_name,
            hospital_lat=h_lat,
            hospital_lon=h_lon,
            incident_id=incident.id
        )

        incident.estimated_arrival_minutes = routing_res.duration_minutes
        
        # Log transition audit logs
        self.audit_agent.record_transition(
            incident=incident,
            status="Ambulance En Route",
            notes=(
                f"Ambulance updated patient location coordinates. "
                f"New Address: {new_address}. "
                f"Remaining Distance: {routing_res.distance_miles} miles. "
                f"New ETA: {routing_res.duration_minutes} minutes."
            )
        )
        
        self.db.commit()
        self.db.refresh(incident)
        return incident

