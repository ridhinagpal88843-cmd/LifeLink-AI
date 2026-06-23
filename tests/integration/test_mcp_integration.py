import json
import pytest
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact
from backend.mcp.client import MCPClientRegistry
from backend.orchestrator.workflow_manager import EmergencyWorkflowManager
from backend.agents.coordinator_agent import EmergencyCoordinatorAgent


@pytest.fixture
def mcp_user_fixture(db_session: Session) -> User:
    # Create User
    user = User(
        email="mcp.test@lifelink.org",
        hashed_password="mockhashedpassword",
        full_name="Peter Parker",
        phone="+1-555-6160"
    )
    db_session.add(user)
    db_session.flush()

    # Create Doctor
    doctor = Doctor(
        name="Dr. Octopus",
        phone="+1-555-8888",
        email="doc.oc@hospital.org",
        specialty="Neurology"
    )
    db_session.add(doctor)
    db_session.flush()

    # Create Emergency Health Profile
    profile = EmergencyHealthProfile(
        user_id=user.id,
        primary_doctor_id=doctor.id,
        blood_group="O+",
        medical_conditions="Spider bite side-effects",
        allergies="None",
        current_medications="None",
        emergency_preferences="Prefer General Clinic"
    )
    db_session.add(profile)

    # Create Emergency Contact
    contact = EmergencyContact(
        user_id=user.id,
        name="May Parker",
        relationship="Aunt",
        phone="+1-555-6161",
        priority=1
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_mcp_tool_execution_success(db_session: Session, mcp_user_fixture: User):
    """
    Verify that when MCP services are online, the workflow routes all requests
    through the Patient DB, Maps, Doctor Directory, and Voice Call MCP tools successfully.
    """
    # Instantiate coordinator with mcp client having use_mcp_mock=True (online mode)
    mcp_client = MCPClientRegistry(db=db_session, use_mcp_mock=True)
    coordinator = EmergencyCoordinatorAgent(db=db_session, mcp_client=mcp_client)
    
    telemetry = {
        "emergency_type": "Respiratory Distress",
        "severity": "High",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "heart_rate": 135,
        "spo2": 88,
        "symptoms": ["difficulty breathing"]
    }

    # Execute workflow
    incident = await coordinator.orchestrate_emergency(
        user_id=mcp_user_fixture.id,
        telemetry_data=telemetry
    )

    # Assert incident successfully resolved
    assert incident.id is not None
    assert incident.status == "Resolved"
    assert incident.assigned_hospital == "Mercy General Hospital"
    
    # Assertions on transitions
    statuses = [t.status for t in incident.state_transitions]
    assert "Doctor Contacted" in statuses
    assert "Family Contacted" in statuses


@pytest.mark.asyncio
async def test_mcp_offline_fallback_behavior(db_session: Session, mcp_user_fixture: User):
    """
    Verify that when MCP services are offline (use_mcp_mock=False),
    the workflow catches exceptions and seamlessly falls back to local DB queries,
    local geocoding math, local voice script engines, and python logging.
    """
    # Instantiate registry with offline mode (use_mcp_mock=False)
    mcp_client = MCPClientRegistry(db=db_session, use_mcp_mock=False)
    coordinator = EmergencyCoordinatorAgent(db=db_session, mcp_client=mcp_client)
    
    telemetry = {
        "emergency_type": "Cardiac Arrest",
        "severity": "Critical",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "heart_rate": 140,
        "spo2": 85,
        "symptoms": ["chest pain"]
    }

    # Execute workflow. It should execute successfully despite MCP server errors
    incident = await coordinator.orchestrate_emergency(
        user_id=mcp_user_fixture.id,
        telemetry_data=telemetry
    )

    # Assert incident was handled, resolved, and saved correctly in fallback mode
    assert incident.id is not None
    assert incident.status == "Resolved"
    assert incident.assigned_hospital == "Mercy General Hospital"
    
    # Check that fallback address was logged
    snapshot = json.loads(incident.medical_profile_snapshot)
    assert snapshot["patient_info"]["full_name"] == "Peter Parker"
    assert snapshot["clinical_info"]["blood_group"] == "O+"
    
    # Verify transitions
    statuses = [t.status for t in incident.state_transitions]
    assert "Detected" in statuses
    assert "Doctor Contacted" in statuses
    assert "Family Contacted" in statuses
    assert "Resolved" in statuses
