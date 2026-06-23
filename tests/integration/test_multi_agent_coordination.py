import json
import pytest
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact
from backend.orchestrator.workflow_manager import EmergencyWorkflowManager


@pytest.fixture
def agent_user_fixture(db_session: Session) -> User:
    # Create User
    user = User(
        email="agent.test@lifelink.org",
        hashed_password="mockhashedpassword",
        full_name="Agent Smith",
        phone="+1-555-4000"
    )
    db_session.add(user)
    db_session.flush()

    # Create Doctor
    doctor = Doctor(
        name="Dr. Sarah Connor",
        phone="+1-555-7000",
        email="sarah.connor@hospital.org",
        specialty="Trauma Care"
    )
    db_session.add(doctor)
    db_session.flush()

    # Create Emergency Health Profile
    profile = EmergencyHealthProfile(
        user_id=user.id,
        primary_doctor_id=doctor.id,
        blood_group="O-",
        medical_conditions="Diabetes",
        allergies="Penicillin",
        current_medications="Metformin",
        emergency_preferences="Mercy Hospital"
    )
    db_session.add(profile)

    # Create Emergency Contact
    contact = EmergencyContact(
        user_id=user.id,
        name="John Connor",
        relationship="Son",
        phone="+1-555-7001",
        priority=1
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_multi_agent_coordination_pipeline(db_session: Session, agent_user_fixture: User):
    """
    Verifies collaborating agent execution:
    1. MedicalProfileAgent loads info.
    2. TriageAgent assesses telemetry.
    3. LocationRoutingAgent geocodes.
    4. DoctorAgent & FamilyAgent alert contacts.
    5. AuditAgent records lifecycle state transitions.
    """
    manager = EmergencyWorkflowManager(db=db_session)
    
    telemetry = {
        "emergency_type": "Hypoxia Emergency",
        "severity": "High",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "heart_rate": 115,
        "spo2": 88,
        "symptoms": ["wheezing", "shortness of breath"]
    }

    # Trigger workflow
    incident = await manager.trigger_emergency_workflow(
        user_id=agent_user_fixture.id,
        telemetry_data=telemetry
    )

    # Assert basic incident details
    assert incident.id is not None
    assert incident.user_id == agent_user_fixture.id
    assert incident.assigned_doctor_id == agent_user_fixture.emergency_health_profile.primary_doctor_id
    assert incident.assigned_hospital == "Mercy General Hospital"
    assert incident.assigned_ambulance == "Ambulance #4"
    assert incident.estimated_arrival_minutes == 7

    # Verify decision log matches agent rationales
    decision_log = json.loads(incident.agent_decision_log)
    assert "triage_summary" in decision_log
    assert "protocol_recommended" in decision_log
    assert len(decision_log["actions_logged"]) == 4

    # Verify state transitions logged by AuditAgent
    transitions = incident.state_transitions
    assert len(transitions) == 8
    statuses = [t.status for t in transitions]
    assert "Detected" in statuses
    assert "Dispatching" in statuses
    assert "Ambulance En Route" in statuses
    assert "Doctor Contacted" in statuses
    assert "Family Contacted" in statuses
    assert "Patient Reached" in statuses
    assert "Hospital Admission" in statuses
    assert "Resolved" in statuses
