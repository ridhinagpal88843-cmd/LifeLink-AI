import pytest
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact
from backend.orchestrator.workflow_manager import EmergencyWorkflowManager


@pytest.fixture
def test_user_fixture(db_session: Session) -> User:
    # Create User
    user = User(
        email="patient.gps@lifelink.org",
        hashed_password="mockhashedpassword",
        full_name="Mark Smith",
        phone="+1-555-9876"
    )
    db_session.add(user)
    db_session.flush()

    # Create Doctor
    doctor = Doctor(
        name="Dr. Charles",
        phone="+1-555-5000",
        email="charles@clinic.org",
        specialty="Emergency Medicine"
    )
    db_session.add(doctor)
    db_session.flush()

    # Create Emergency Health Profile
    profile = EmergencyHealthProfile(
        user_id=user.id,
        primary_doctor_id=doctor.id,
        blood_group="A+",
        medical_conditions="Hypertension",
        allergies="Shellfish",
        current_medications="Lisinopril",
        emergency_preferences="Mercy Hospital preferred"
    )
    db_session.add(profile)

    # Create Contact
    contact = EmergencyContact(
        user_id=user.id,
        name="Mary Smith",
        relationship="Spouse",
        phone="+1-555-9875",
        priority=1
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_live_location_updates_integration(db_session: Session, test_user_fixture: User):
    """
    Integration test asserting that:
    1. An incident is detected and dispatched with geocoded addresses.
    2. Live coordinate updates from the ambulance are processed.
    3. State transitions register the remaining distances and revised ETAs.
    """
    manager = EmergencyWorkflowManager(db=db_session)
    
    # Telemetry near Civic Center SF
    telemetry = {
        "emergency_type": "Severe Chest Pain",
        "severity": "Critical",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "heart_rate": 130,
        "spo2": 87,
        "symptoms": ["chest pain", "shortness of breath"]
    }

    # Trigger emergency
    incident = await manager.trigger_emergency_workflow(
        user_id=test_user_fixture.id,
        telemetry_data=telemetry
    )

    # Assert geocoding worked on setup
    assert incident.id is not None
    assert incident.status == "Resolved"
    assert incident.latitude == 37.7749
    assert incident.longitude == -122.4194
    assert incident.assigned_hospital == "Mercy General Hospital"
    
    # Check that initial geocoded address was logged in first transition
    init_transition = incident.state_transitions[0]
    assert "Market St" in init_transition.notes

    # Now let's trigger a live location update (Ambulance moves closer to Mercy General Hospital)
    # New Coordinates (closer to 37.7849, -122.4094)
    updated_lat = 37.7800
    updated_lon = -122.4130
    
    updated_incident = await manager.update_incident_location(
        incident_id=incident.id,
        latitude=updated_lat,
        longitude=updated_lon
    )

    # Assert database updated coordinates correctly
    assert updated_incident.latitude == updated_lat
    assert updated_incident.longitude == updated_lon
    
    # Verify new state transition exists for live updates
    new_transitions = updated_incident.state_transitions
    assert len(new_transitions) > 8  # Original 8 + Live updates
    
    latest_transition = new_transitions[-1]
    assert latest_transition.status == "Ambulance En Route"
    assert "Ambulance updated patient location" in latest_transition.notes
    assert "Remaining Distance" in latest_transition.notes
    assert "New ETA" in latest_transition.notes
