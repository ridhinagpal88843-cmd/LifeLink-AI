import json
import pytest
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact
from backend.orchestrator.workflow_manager import EmergencyWorkflowManager


@pytest.fixture
def sample_user_with_medical_info(db_session: Session) -> User:
    """
    Creates a user, doctor, emergency profile, and emergency contacts in the db session.
    """
    # 1. Create User
    user = User(
        email="patient.test@lifelink.org",
        hashed_password="mockhashedpassword",
        full_name="John Doe",
        phone="+1-555-0001"
    )
    db_session.add(user)
    db_session.flush()

    # 2. Create Doctor
    doctor = Doctor(
        name="Dr. Vance",
        phone="+1-555-9999",
        email="vance@clinic.org",
        specialty="General Medicine"
    )
    db_session.add(doctor)
    db_session.flush()

    # 3. Create Emergency Health Profile
    profile = EmergencyHealthProfile(
        user_id=user.id,
        primary_doctor_id=doctor.id,
        blood_group="O+",
        medical_conditions="Asthma",
        allergies="Nuts",
        current_medications="Albuterol inhaler",
        emergency_preferences="Prefer City Hospital"
    )
    db_session.add(profile)

    # 4. Create Emergency Contacts
    contact = EmergencyContact(
        user_id=user.id,
        name="Jane Doe",
        relationship="Spouse",
        phone="+1-555-0002",
        priority=1
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_emergency_workflow_manager_execution(db_session: Session, sample_user_with_medical_info: User):
    """
    Test that triggering the emergency workflow asynchronously:
    1. Creates an EmergencyIncident record.
    2. Snapshots patient info correctly.
    3. Runs triage and parallel dispatch.
    4. Logs all state transitions in the lifecycle.
    """
    manager = EmergencyWorkflowManager(db=db_session)
    telemetry = {
        "emergency_type": "Respiratory Distress",
        "severity": "High",
        "latitude": 37.7749,
        "longitude": -122.4194
    }

    # Execute workflow asynchronously
    incident = await manager.trigger_emergency_workflow(
        user_id=sample_user_with_medical_info.id,
        telemetry_data=telemetry
    )

    # Assertions
    assert incident.id is not None
    assert incident.user_id == sample_user_with_medical_info.id
    assert incident.assigned_doctor_id == sample_user_with_medical_info.emergency_health_profile.primary_doctor_id
    assert incident.emergency_type == "Respiratory Distress"
    assert incident.severity == "Critical"  # Overwritten by mock TriageAgent
    assert incident.status == "Resolved"  # Final state reached in mock lifecycle
    assert incident.assigned_hospital == "Mercy General Hospital"
    assert incident.assigned_ambulance == "Ambulance #4"
    assert incident.estimated_arrival_minutes == 7

    # Verify Snapshot contents
    snapshot = json.loads(incident.medical_profile_snapshot)
    assert snapshot["patient_info"]["full_name"] == "John Doe"
    assert snapshot["clinical_info"]["blood_group"] == "O+"
    assert snapshot["clinical_info"]["allergies"] == "Nuts"
    assert snapshot["primary_doctor"]["name"] == "Dr. Vance"
    assert len(snapshot["emergency_contacts"]) == 1
    assert snapshot["emergency_contacts"][0]["name"] == "Jane Doe"
    
    # Verify State Transitions
    transitions = incident.state_transitions
    assert len(transitions) == 8  # Detected, Dispatching, Ambulance En Route, Doctor Contacted, Family Contacted, Patient Reached, Hospital Admission, Resolved
    
    statuses = [t.status for t in transitions]
    expected_statuses = [
        "Detected", 
        "Dispatching", 
        "Ambulance En Route", 
        "Doctor Contacted", 
        "Family Contacted", 
        "Patient Reached", 
        "Hospital Admission", 
        "Resolved"
    ]
    assert statuses == expected_statuses
    
    # Ensure timestamps are recorded
    for transition in transitions:
        assert transition.timestamp is not None
        assert transition.incident_id == incident.id
