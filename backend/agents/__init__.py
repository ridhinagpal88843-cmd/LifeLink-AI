"""
Agents Layer (Google ADK & Telemetry Classifiers)
=================================================

This package contains the collaborating AI agents:
- TriageAgent: Vitals diagnostic classifier.
- LocationRoutingAgent: Geocoding and route calculation.
- MedicalProfileAgent: Eager-loads patient history context.
- DoctorCommunicationAgent: Outbound physician notifications.
- FamilyCommunicationAgent: Outbound family member notifications.
- AuditAgent: Immutably records transitions and action audits.
- EmergencyCoordinatorAgent: Orchestrator driving multi-agent workflows.
"""

from backend.agents.triage_agent import TriageAgent, TriageResult
from backend.agents.location_agent import LocationRoutingAgent
from backend.agents.medical_profile_agent import MedicalProfileAgent
from backend.agents.doctor_agent import DoctorCommunicationAgent
from backend.agents.family_agent import FamilyCommunicationAgent
from backend.agents.audit_agent import AuditAgent
from backend.agents.coordinator_agent import EmergencyCoordinatorAgent

__all__ = [
    "TriageAgent",
    "TriageResult",
    "LocationRoutingAgent",
    "MedicalProfileAgent",
    "DoctorCommunicationAgent",
    "FamilyCommunicationAgent",
    "AuditAgent",
    "EmergencyCoordinatorAgent"
]
