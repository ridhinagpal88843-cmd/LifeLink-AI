import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.models.emergency_incident import EmergencyIncident
from backend.mcp.client import MCPClientRegistry
from backend.agents.medical_profile_agent import MedicalProfileAgent
from backend.agents.triage_agent import TriageAgent
from backend.agents.location_agent import LocationRoutingAgent
from backend.agents.doctor_agent import DoctorCommunicationAgent
from backend.agents.family_agent import FamilyCommunicationAgent
from backend.agents.audit_agent import AuditAgent

logger = logging.getLogger(__name__)

# Coordinates mapping for hospital coordinates
HOSPITAL_COORDINATES = {
    "Mercy General Hospital": (37.7849, -122.4094),
    "City General Hospital": (37.7650, -122.4400)
}


class EmergencyCoordinatorAgent:
    """
    Multi-Agent Coordinator orchestrating:
    - MedicalProfileAgent (Patient DB MCP)
    - LocationRoutingAgent (Maps MCP)
    - TriageAgent (AI Classifier)
    - DoctorCommunicationAgent (Directory & Voice MCP)
    - FamilyCommunicationAgent (Voice MCP)
    - AuditAgent (Logging MCP)
    """

    def __init__(self, db: Session, mcp_client: Optional[MCPClientRegistry] = None):
        self.db = db
        self.mcp_client = mcp_client or MCPClientRegistry(db)
        
        # Inject MCP integration layer into all sub-agents
        self.profile_agent = MedicalProfileAgent(db, self.mcp_client)
        self.triage_agent = TriageAgent()
        self.location_agent = LocationRoutingAgent(self.mcp_client)
        self.doctor_agent = DoctorCommunicationAgent(self.mcp_client)
        self.family_agent = FamilyCommunicationAgent(self.mcp_client)
        self.audit_agent = AuditAgent(db, self.mcp_client)

    async def orchestrate_emergency(self, user_id: str, telemetry_data: Dict[str, Any]) -> EmergencyIncident:
        """
        Coordinates the end-to-end multi-agent execution pipeline.
        """
        # 1. Retrieve patient medical records via Profile Agent (Patient DB MCP)
        history = self.profile_agent.retrieve_patient_history(user_id)
        
        # 2. Reverse geocode location via Location Agent (Maps MCP)
        lat = telemetry_data.get("latitude", 37.7749)
        lon = telemetry_data.get("longitude", -122.4194)
        geocode_result = self.location_agent.reverse_geocode(lat, lon)
        patient_address = geocode_result.address

        # 3. Create active incident record
        incident = self._initialize_incident(user_id, telemetry_data, history)
        
        # Log initial Detected state transition (Logging MCP)
        self.audit_agent.record_transition(
            incident=incident,
            status="Detected",
            notes=f"Emergency telemetry received for {history['patient_info']['full_name']} at: {patient_address}."
        )

        try:
            # 4. AI Triage Assessment (Triage Agent)
            vitals = {
                "heart_rate": telemetry_data.get("heart_rate", 80),
                "spo2": telemetry_data.get("spo2", 98),
                "systolic": telemetry_data.get("systolic"),
                "diastolic": telemetry_data.get("diastolic")
            }
            symptoms = telemetry_data.get("symptoms", ["Unknown"])
            triage_res = self.triage_agent.triage(vitals, symptoms, history["clinical_info"])
            
            incident.severity = triage_res.severity
            self.db.commit()

            # 5. Check Triage confidence and criticality for parallel dispatch
            if triage_res.confidence_score >= 0.8 and triage_res.severity in ["Critical", "High"]:
                self.audit_agent.record_transition(
                    incident=incident,
                    status="Dispatching",
                    notes="High-confidence critical event. Dispatching sub-agents in parallel."
                )

                # Define hospital coordinates
                hospital_name = "Mercy General Hospital"
                h_lat, h_lon = HOSPITAL_COORDINATES[hospital_name]
                
                # Setup routing parameters (Maps MCP)
                routing_res = self.location_agent.calculate_routing(
                    from_lat=lat,
                    from_lon=lon,
                    hospital_name=hospital_name,
                    hospital_lat=h_lat,
                    hospital_lon=h_lon,
                    incident_id=incident.id
                )

                # Populate incident fields
                incident.assigned_hospital = hospital_name
                incident.assigned_ambulance = "Ambulance #4"
                incident.estimated_arrival_minutes = routing_res.duration_minutes
                self.db.commit()

                # Build incident details dictionary for communication agents
                incident_details = {
                    "emergency_type": triage_res.emergency_type,
                    "severity": triage_res.severity,
                    "location": patient_address,
                    "assigned_hospital": hospital_name,
                    "eta_minutes": routing_res.duration_minutes
                }

                # Concurrently execute doctor call (Doctor Agent) and family calls (Family Agent)
                doctor_task = self.doctor_agent.alert_family_doctor(
                    doctor_info=history["primary_doctor"],
                    patient_name=history["patient_info"]["full_name"],
                    incident_details=incident_details,
                    medical_history=history["clinical_info"]
                )
                family_task = self.family_agent.alert_family_contacts(
                    contacts=history["emergency_contacts"],
                    patient_name=history["patient_info"]["full_name"],
                    incident_details=incident_details
                )
                
                # Execute calls simultaneously via Voice MCP
                doctor_call, family_calls = await asyncio.gather(doctor_task, family_task)

                # Log lifecycle transitions (Logging MCP)
                self.audit_agent.record_transition(
                    incident=incident,
                    status="Ambulance En Route",
                    notes=f"Ambulance dispatched. Distance: {routing_res.distance_miles} miles. ETA: {routing_res.duration_minutes} minutes."
                )

                if doctor_call.get("status") in ["success", "fallback", "queued"]:
                    self.audit_agent.record_transition(
                        incident=incident,
                        status="Doctor Contacted",
                        notes=f"Outbound voice alert completed to primary physician Dr. {history['primary_doctor']['name']}."
                    )

                if family_calls:
                    self.audit_agent.record_transition(
                        incident=incident,
                        status="Family Contacted",
                        notes=f"Alert call queued to {len(family_calls)} emergency contacts."
                    )

                # Record audits via Audit Agent (Logging MCP)
                audit_summaries = [
                    f"Ambulance dispatched: Ambulance #4 (ETA {routing_res.duration_minutes}m)",
                    f"Doctor call placed: {doctor_call.get('recipient') or doctor_call.get('call_id')}",
                    f"Family contacts notified: {len(family_calls)} calls queued",
                    f"Live tracking: {routing_res.live_tracking_url}"
                ]
                self.audit_agent.log_actions(incident.id, audit_summaries)

                decision_log = {
                    "triage_summary": triage_res.triage_summary,
                    "protocol_recommended": triage_res.emergency_protocol,
                    "actions_logged": audit_summaries,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                incident.agent_decision_log = json.dumps(decision_log)
                self.db.commit()

                # Simulate rest of incident progression
                await asyncio.sleep(0.01)
                self.audit_agent.record_transition(incident, "Patient Reached", "Ambulance arrived at patient's location.")
                await asyncio.sleep(0.01)
                self.audit_agent.record_transition(incident, "Hospital Admission", f"Patient admitted to {hospital_name} Emergency department.")
                await asyncio.sleep(0.01)
                self.audit_agent.record_transition(incident, "Resolved", "Incident completed and resolved.")

            else:
                # Sequential Flow fallback
                self.audit_agent.record_transition(incident, "Dispatching", "Sequential triage pipeline initiated.")
                incident.assigned_hospital = "Mercy General Hospital"
                incident.assigned_ambulance = "Ambulance #4"
                incident.estimated_arrival_minutes = 10
                self.db.commit()

                self.audit_agent.record_transition(incident, "Ambulance En Route", "Ambulance unit dispatched sequentially.")
                
                # Notify doctor
                incident_details = {
                    "emergency_type": triage_res.emergency_type,
                    "severity": triage_res.severity,
                    "location": patient_address,
                    "assigned_hospital": incident.assigned_hospital,
                    "eta_minutes": 10
                }
                await self.doctor_agent.alert_family_doctor(
                    doctor_info=history["primary_doctor"],
                    patient_name=history["patient_info"]["full_name"],
                    incident_details=incident_details,
                    medical_history=history["clinical_info"]
                )
                self.audit_agent.record_transition(incident, "Doctor Contacted", "Physician notified sequentially.")

                # Notify contacts
                await self.family_agent.alert_family_contacts(
                    contacts=history["emergency_contacts"],
                    patient_name=history["patient_info"]["full_name"],
                    incident_details=incident_details
                )
                self.audit_agent.record_transition(incident, "Family Contacted", "Contacts notified sequentially.")

                await asyncio.sleep(0.01)
                self.audit_agent.record_transition(incident, "Resolved", "Incident completed sequentially.")

            self.db.commit()
            self.db.refresh(incident)
            return incident

        except Exception as e:
            self.audit_agent.record_transition(incident, "Closed", f"Pipeline error: {str(e)}")
            incident.agent_decision_log = json.dumps({"pipeline_error": str(e)})
            self.db.commit()
            raise e

    def _initialize_incident(self, user_id: str, telemetry: Dict[str, Any], history: Dict[str, Any]) -> EmergencyIncident:
        incident = EmergencyIncident(
            user_id=user_id,
            assigned_doctor_id=history["primary_doctor"].get("id") if history["primary_doctor"] else None,
            emergency_type=telemetry.get("emergency_type", "Unknown Telemetry Alert"),
            severity=telemetry.get("severity", "High"),
            status="Detected",
            latitude=telemetry.get("latitude"),
            longitude=telemetry.get("longitude"),
            medical_profile_snapshot=json.dumps(history)
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident
