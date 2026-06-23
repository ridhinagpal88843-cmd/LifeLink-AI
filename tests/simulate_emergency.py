import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Add workspace directory to python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, workspace_root)

# ==========================================
# 1. SETUP MOCKS FOR ABSENT PACKAGES
# ==========================================

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock Pydantic
class MockBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def dict(self):
        return self.__dict__

class MockField:
    def __init__(self, *args, **kwargs):
        pass

pydantic_mock = MagicMock()
pydantic_mock.BaseModel = MockBaseModel
pydantic_mock.Field = MockField
sys.modules['pydantic'] = pydantic_mock

# Mock SQLAlchemy and Database
sqlalchemy_mock = MagicMock()
sys.modules['sqlalchemy'] = sqlalchemy_mock
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()

class MockBase:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

db_mock = MagicMock()
db_mock.Base = MockBase
sys.modules['backend.database'] = db_mock

# Mock Google GenAI SDK
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()

# ==========================================
# 2. DEFINE SYSTEM MODELS AND SCHEMA STUBS
# ==========================================

# Stub user models that mimic the database structure
class User(MockBase):
    id = 'id'
    email = 'email'
    hashed_password = 'hashed_password'
    full_name = 'full_name'
    phone = 'phone'

class Doctor(MockBase):
    id = 'id'
    name = 'name'
    phone = 'phone'
    email = 'email'
    specialty = 'specialty'

class EmergencyHealthProfile(MockBase):
    id = 'id'
    user_id = 'user_id'
    primary_doctor_id = 'primary_doctor_id'
    blood_group = 'blood_group'
    medical_conditions = 'medical_conditions'
    allergies = 'allergies'
    current_medications = 'current_medications'
    emergency_preferences = 'emergency_preferences'

class EmergencyContact(MockBase):
    id = 'id'
    user_id = 'user_id'
    name = 'name'
    relationship = 'relationship'
    phone = 'phone'
    priority = 'priority'

class EmergencyIncident(MockBase):
    id = 'id'
    user_id = 'user_id'
    assigned_doctor_id = 'assigned_doctor_id'
    emergency_type = 'emergency_type'
    severity = 'severity'
    status = 'status'
    latitude = 'latitude'
    longitude = 'longitude'
    medical_profile_snapshot = 'medical_profile_snapshot'
    assigned_hospital = 'assigned_hospital'
    assigned_ambulance = 'assigned_ambulance'
    estimated_arrival_minutes = 'estimated_arrival_minutes'
    agent_decision_log = 'agent_decision_log'
    created_at = 'created_at'
    updated_at = 'updated_at'

class IncidentStateTransition(MockBase):
    id = 'id'
    incident_id = 'incident_id'
    status = 'status'
    notes = 'notes'
    timestamp = 'timestamp'

# Patch modules in sys.modules so imports find our stubs
models_module = MagicMock()
models_module.User = User
models_module.Doctor = Doctor
models_module.EmergencyHealthProfile = EmergencyHealthProfile
models_module.EmergencyContact = EmergencyContact
models_module.EmergencyIncident = EmergencyIncident
models_module.IncidentStateTransition = IncidentStateTransition
sys.modules['backend.models'] = models_module
sys.modules['backend.models.user'] = models_module
sys.modules['backend.models.doctor'] = models_module
sys.modules['backend.models.emergency_health_profile'] = models_module
sys.modules['backend.models.emergency_contact'] = models_module
sys.modules['backend.models.emergency_incident'] = models_module

# ==========================================
# 3. IMPORT REAL AGENT & COORDINATOR LOGIC
# ==========================================
# Now that mocks are active, we can import the agent classes safely
from backend.agents.coordinator_agent import EmergencyCoordinatorAgent
from backend.agents.triage_agent import TriageAgent, TriageResult
from backend.agents.location_agent import LocationRoutingAgent
from backend.agents.doctor_agent import DoctorCommunicationAgent
from backend.agents.family_agent import FamilyCommunicationAgent
from backend.agents.audit_agent import AuditAgent
from backend.mcp.client import MCPClientRegistry

# ==========================================
# 4. IMPLEMENT MOCK DATABASE SESSION
# ==========================================

class MockQuery:
    def __init__(self, result):
        self.result = result
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return self.result
    def all(self):
        return [self.result] if self.result else []
    def order_by(self, *args, **kwargs):
        return self

class MockSession:
    def __init__(self, user, doctor, profile, contacts):
        self.user = user
        self.doctor = doctor
        self.profile = profile
        self.contacts = contacts
        self.incidents = []
        self.transitions = []

    def add(self, obj):
        if isinstance(obj, EmergencyIncident):
            self.incidents.append(obj)
            obj.state_transitions = []
        elif isinstance(obj, IncidentStateTransition):
            self.transitions.append(obj)
            # Link to the appropriate incident
            for inc in self.incidents:
                if inc.id == obj.incident_id:
                    inc.state_transitions.append(obj)
                    break

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        if model.__name__ == 'User':
            return MockQuery(self.user)
        elif model.__name__ == 'Doctor':
            return MockQuery(self.doctor)
        elif model.__name__ == 'EmergencyIncident':
            return MockQuery(self.incidents[0] if self.incidents else None)
        return MockQuery(None)

# ==========================================
# 5. SIMULATION EXECUTION MAIN ENGINE
# ==========================================

async def main():
    print("=" * 70)
    print("LIFELINK AI EMERGENCY RESPONSE SIMULATION ENGINE")
    print("=" * 70)

    # Create mock entities
    print("[1/8] Seeding Mock Patient Medical Records & Contacts...")
    
    mock_doctor = Doctor(
        id="doc-uuid-111",
        name="Dr. Sarah Connor",
        phone="+1-555-7000",
        email="sarah.connor@hospital.org",
        specialty="Trauma Care"
    )

    mock_profile = EmergencyHealthProfile(
        primary_doctor_id="doc-uuid-111",
        primary_doctor=mock_doctor,
        blood_group="AB-",
        medical_conditions="Type 1 Diabetes, Severe Asthma",
        allergies="Latex, Penicillin",
        current_medications="Insulin, Albuterol Inhaler",
        emergency_preferences="Transport to Mercy General Hospital"
    )

    mock_contacts = [
        EmergencyContact(name="Clara Pierce", relationship="Spouse", phone="+1-555-1111", priority=1),
        EmergencyContact(name="John Pierce", relationship="Brother", phone="+1-555-2222", priority=2)
    ]

    mock_user = User(
        id="patient-uuid-222",
        full_name="Alexander Pierce",
        email="alexander.pierce@lifelink.ai",
        phone="+1-555-0811",
        emergency_health_profile=mock_profile,
        emergency_contacts=mock_contacts
    )

    # Setup isolated mock database session
    db_session = MockSession(mock_user, mock_doctor, mock_profile, mock_contacts)

    # Setup MCP client
    print("[2/8] Initializing MCP Integration Registry (Online Mock Mode)...")
    mcp_client = MCPClientRegistry(db=db_session, use_mcp_mock=True)

    # Instantiate coordinator agent
    print("[3/8] Spawning Multi-Agent emergency coordinator...")
    coordinator = EmergencyCoordinatorAgent(db=db_session, mcp_client=mcp_client)

    # Ingest critical vital signals (respiratory distress asthma trigger)
    print("\n" + "-" * 70)
    print("EMERGENCY TELEMETRY SIGNAL INGESTED")
    print("-" * 70)
    telemetry = {
        "emergency_type": "Respiratory Distress",
        "severity": "High",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "heart_rate": 125,
        "spo2": 88,
        "symptoms": ["wheezing", "difficulty breathing"]
    }
    print(f"Vitals: HR={telemetry['heart_rate']} bpm, SpO2={telemetry['spo2']}%")
    print(f"Symptoms: {', '.join(telemetry['symptoms'])}")
    print(f"GPS Coordinates: {telemetry['latitude']}, {telemetry['longitude']}")

    # 4. Trigger Orchestration Workflow
    print("\n[4/8] Running Emergency Coordinator Orchestration pipeline...")
    incident = await coordinator.orchestrate_emergency(user_id=mock_user.id, telemetry_data=telemetry)

    # Check state transitions and details
    print("\n" + "-" * 70)
    print("CO-ORDINATION REPORT")
    print("-" * 70)
    print(f"Incident ID: {incident.id}")
    print(f"Severity Classification: {incident.severity}")
    print(f"Assigned Hospital: {incident.assigned_hospital}")
    print(f"Assigned Ambulance: {incident.assigned_ambulance}")
    print(f"Estimated Travel Duration: {incident.estimated_arrival_minutes} minutes")

    print("\n[5/8] Outbound Voice Communication Alert scripts generated:")
    decision_log = json.loads(incident.agent_decision_log)
    print("AI Triage Summary:")
    print(f"  {decision_log['triage_summary']}")
    print("Recommended Protocol:")
    print(f"  {decision_log['protocol_recommended']}")

    print("\n[6/8] Timeline audit of chronological transitions logged:")
    for transition in incident.state_transitions:
        print(f"  [{transition.timestamp.strftime('%H:%M:%S')}] {transition.status:<20} | Notes: {transition.notes}")

    # 7. Simulate Location Updates
    print("\n[7/8] Simulating Ambulance Live coordinates telemetry updates...")
    print("Ambulance updates patient coordinates while en route to hospital.")
    
    # Simulate first update
    print("Updating location: 37.7800, -122.4150")
    # Re-geocode & calculate routing
    loc_agent = LocationRoutingAgent(mcp_client)
    h_lat, h_lon = (37.7849, -122.4094) # Mercy General Hospital
    routing_res = loc_agent.calculate_routing(
        from_lat=37.7800,
        from_lon=-122.4150,
        hospital_name=incident.assigned_hospital,
        hospital_lat=h_lat,
        hospital_lon=h_lon,
        incident_id=incident.id
    )
    incident.latitude = 37.7800
    incident.longitude = -122.4150
    incident.estimated_arrival_minutes = routing_res.duration_minutes
    
    audit_agent = AuditAgent(db_session, mcp_client)
    audit_agent.record_transition(
        incident=incident,
        status="Ambulance En Route",
        notes=f"Ambulance updated patient location. New ETA: {routing_res.duration_minutes}m, Remaining Distance: {routing_res.distance_miles} miles."
    )

    # Simulate arrival
    print("Updating location (Arrival at Hospital): 37.7849, -122.4094")
    incident.latitude = 37.7849
    incident.longitude = -122.4094
    incident.estimated_arrival_minutes = 0
    audit_agent.record_transition(
        incident=incident,
        status="Patient Reached",
        notes="Ambulance arrived at Mercy General Hospital Emergency Room."
    )

    # 8. Close / Resolve Incident
    print("\n[8/8] Closing Incident with Resolved status...")
    incident.status = "Resolved"
    audit_agent.record_transition(
        incident=incident,
        status="Resolved",
        notes="Patient safely admitted. Incident closed."
    )

    print("\n" + "=" * 70)
    print("SIMULATION TIMELINE RESOLVED SUCCESSFULLY")
    print("=" * 70)
    for transition in incident.state_transitions:
        print(f"  [{transition.timestamp.strftime('%H:%M:%S')}] {transition.status:<20} | Notes: {transition.notes}")

if __name__ == '__main__':
    asyncio.run(main())
