import streamlit as st
import requests
import time
import pandas as pd
import json

# Setup page layout
st.set_page_config(
    page_title="LifeLink AI - Emergency Coordination Center",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern glassmorphism feel
st.markdown("""
<style>
    .reportview-container {
        background-color: #0e1117;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff4b4b, #ff7e40);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #1e222b;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .agent-tag {
        background-color: #2b303c;
        color: #ff7e40;
        padding: 0.2rem 0.6rem;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://127.0.0.1:8000"
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "active_incident" not in st.session_state:
    st.session_state.active_incident = None

# Sidebar Navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/ambulance.png", width=70)
    st.markdown("## Navigation")
    menu = st.radio(
        "Go to",
        ["Home Dashboard", "Patient Profile", "Emergency Incident", "Live Location Tracking", "Incident History", "Settings"]
    )
    
    st.divider()
    st.markdown("### System Status")
    try:
        res = requests.get(f"{st.session_state.api_url}/", timeout=1.0)
        if res.status_code == 200:
            st.success("Backend Connected")
        else:
            st.warning("Backend Connected (Degraded)")
    except Exception:
        st.error("Backend Disconnected")

# Helper function to auto-seed a mock patient in database on startup
def auto_seed_patient():
    """
    Checks if a default test patient exists in the db, otherwise registers one.
    """
    default_email = "alexander.pierce@lifelink.ai"
    try:
        # We try to sign up the patient
        signup_payload = {
            "email": default_email,
            "password": "demopassword123",
            "full_name": "Alexander Pierce",
            "phone": "+1-555-0811",
            "emergency_health_profile": {
                "blood_group": "AB-",
                "medical_conditions": "Type 1 Diabetes, Severe Asthma",
                "allergies": "Latex, Penicillin",
                "current_medications": "Insulin, Albuterol Inhaler",
                "emergency_preferences": "Transport to Mercy General Hospital"
            },
            "primary_doctor": {
                "name": "Dr. Sarah Connor",
                "phone": "+1-555-7000",
                "email": "sarah.connor@hospital.org",
                "specialty": "Trauma Care"
            },
            "emergency_contacts": [
                {
                    "name": "Clara Pierce",
                    "relationship": "Spouse",
                    "phone": "+1-555-1111",
                    "priority": 1
                },
                {
                    "name": "John Pierce",
                    "relationship": "Brother",
                    "phone": "+1-555-2222",
                    "priority": 2
                }
            ]
        }
        res = requests.post(f"{st.session_state.api_url}/signup", json=signup_payload)
        if res.status_code == 201:
            data = res.json()
            st.session_state.patient_id = data["id"]
        elif res.status_code == 400: # Already registered
            # Find the patient by logging in
            login_payload = {"email": default_email, "password": "demopassword123"}
            login_res = requests.post(f"{st.session_state.api_url}/login", json=login_payload)
            if login_res.status_code == 200:
                token = login_res.json()["access_token"]
                profile_res = requests.get(f"{st.session_state.api_url}/profile", headers={"Authorization": f"Bearer {token}"})
                if profile_res.status_code == 200:
                    st.session_state.patient_id = profile_res.json()["id"]
    except Exception as e:
        logger_err = str(e)

# Seed patient on startup
if not st.session_state.patient_id:
    auto_seed_patient()

# ==========================================
# 1. HOME DASHBOARD
# ==========================================
if menu == "Home Dashboard":
    st.markdown('<h1 class="main-title">LifeLink AI Coordination Center</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Multi-Agent Telemetry & Dispatch Center")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #ff4b4b;">
            <h3 style='margin:0;color:#ff4b4b;'>Active Incidents</h3>
            <h1 style='margin:0;color:white;'>1</h1>
            <p style='margin:0;color:#888;'>Paramedics responding</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #00c853;">
            <h3 style='margin:0;color:#00c853;'>Available Ambulances</h3>
            <h1 style='margin:0;color:white;'>8</h1>
            <p style='margin:0;color:#888;'>GPS tracked & online</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #2979ff;">
            <h3 style='margin:0;color:#2979ff;'>Hospital Bed Capacity</h3>
            <h1 style='margin:0;color:white;'>32</h1>
            <p style='margin:0;color:#888;'>ICU / Emergency Beds</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Trigger Emergency Simulation")
    st.info("Simulate emergency signals arriving from a patient's wearable device to test the AI agent pipeline.")
    
    col_trigger_1, col_trigger_2 = st.columns(2)
    with col_trigger_1:
        sim_emergency_type = st.selectbox(
            "Select Telemetry Emergency Condition",
            ["Cardiac Arrest", "Asthma Attack", "Severe Facial Droop & Speech Loss", "Anxiety & Palpitations"]
        )
        sim_latitude = st.number_input("Patient Latitude", value=37.7749, format="%.4f")
    with col_trigger_2:
        sim_severity = st.selectbox("Select Severity Level", ["Critical", "High", "Moderate"])
        sim_longitude = st.number_input("Patient Longitude", value=-122.4194, format="%.4f")

    trigger_btn = st.button("Trigger Emergency Alert 🚨", use_container_width=True)

    if trigger_btn:
        if not st.session_state.patient_id:
            st.error("No registered Patient ID found. Please go to Patient Profile to register first.")
        else:
            with st.spinner("Multi-Agent Coordination Pipeline running..."):
                # Call POST /emergency/trigger
                trigger_payload = {
                    "emergency_type": sim_emergency_type,
                    "severity": sim_severity,
                    "latitude": sim_latitude,
                    "longitude": sim_longitude
                }
                res = requests.post(
                    f"{st.session_state.api_url}/emergency/trigger?user_id={st.session_state.patient_id}",
                    json=trigger_payload
                )
                if res.status_code == 201:
                    st.session_state.active_incident = res.json()
                    st.success("Emergency incident logged and coordinated successfully!")
                    st.balloons()
                else:
                    st.error(f"Failed to trigger incident: {res.text}")

# ==========================================
# 2. PATIENT PROFILE
# ==========================================
elif menu == "Patient Profile":
    st.markdown('<h1 class="main-title">Patient Profile & Clinical History</h1>', unsafe_allow_html=True)
    st.markdown("### Managed by: <span class=\"agent-tag\">Medical Profile Agent</span>", unsafe_allow_html=True)

    if not st.session_state.patient_id:
        st.warning("No Patient profile loaded. Auto-seeding a default patient profile in the backend database...")
        auto_seed_patient()

    # Load Patient Profile from DB directly
    try:
        # Query User Profile via Database Fallback or MCP
        # For display, let's load all fields
        res = requests.get(f"{st.session_state.api_url}/emergency/history?user_id={st.session_state.patient_id}")
        # To show profile, we will do a mock search in the database for the user details
        from backend.database import SessionLocal
        from backend.models.user import User
        db = SessionLocal()
        user = db.query(User).filter(User.id == st.session_state.patient_id).first()
        
        if user:
            col_profile_1, col_profile_2 = st.columns(2)
            with col_profile_1:
                st.subheader("Personal Information")
                st.write(f"**Full Name**: {user.full_name}")
                st.write(f"**Email**: {user.email}")
                st.write(f"**Phone**: {user.phone}")
                st.write(f"**Patient ID (UUID)**: {user.id}")

                st.subheader("Primary Physician")
                doctor = user.emergency_health_profile.primary_doctor
                if doctor:
                    st.write(f"**Doctor Name**: {doctor.name}")
                    st.write(f"**Specialty**: {doctor.specialty}")
                    st.write(f"**Phone**: {doctor.phone}")
                else:
                    st.write("No primary physician registered.")

            with col_profile_2:
                st.subheader("Emergency Health Profile")
                profile = user.emergency_health_profile
                st.write(f"**Blood Group**: {profile.blood_group}")
                st.write(f"**Existing Conditions**: {profile.medical_conditions}")
                st.write(f"**Allergies**: {profile.allergies}")
                st.write(f"**Current Medications**: {profile.current_medications}")
                st.write(f"**Emergency Preferences**: {profile.emergency_preferences}")

                st.subheader("Emergency Contacts (Top 5)")
                for contact in user.emergency_contacts:
                    st.write(f"- **{contact.name}** ({contact.relationship}): {contact.phone} [Priority {contact.priority}]")
        db.close()
    except Exception as e:
        st.error(f"Error fetching profile details: {e}")

# ==========================================
# 3. EMERGENCY INCIDENT
# ==========================================
elif menu == "Emergency Incident":
    st.markdown('<h1 class="main-title">Active Emergency Incident</h1>', unsafe_allow_html=True)
    st.markdown("### Managed by: <span class=\"agent-tag\">Emergency Coordinator Agent</span>", unsafe_allow_html=True)

    if not st.session_state.active_incident:
        st.info("No active emergency incident. Go to Home Dashboard to simulate an alert.")
    else:
        # Reload latest details from backend
        try:
            res = requests.get(f"{st.session_state.api_url}/emergency/{st.session_state.active_incident['id']}")
            if res.status_code == 200:
                st.session_state.active_incident = res.json()
        except Exception as e:
            st.error(f"Error syncing incident details: {e}")

        incident = st.session_state.active_incident
        
        # Display Info
        col_inc_1, col_inc_2 = st.columns(2)
        with col_inc_1:
            st.subheader("Incident Vitals")
            st.write(f"**Incident ID (UUID)**: {incident['id']}")
            st.write(f"**Reported Emergency**: {incident['emergency_type']}")
            st.write(f"**Assigned Severity**: {incident['severity']}")
            st.write(f"**Current Lifecycle Status**: :red[{incident['status']}]")
            st.write(f"**Latitude/Longitude**: {incident['latitude']}, {incident['longitude']}")
            
            st.subheader("AI Agent Decision Logs")
            if incident.get("agent_decision_log"):
                decision_log = json.loads(incident["agent_decision_log"])
                st.json(decision_log)
            else:
                st.write("No agent decision logs posted yet.")

        with col_inc_2:
            st.subheader("Dispatch Details")
            st.write(f"**Assigned Hospital**: {incident.get('assigned_hospital') or 'Calculating...'}")
            st.write(f"**Dispatched Ambulance**: {incident.get('assigned_ambulance') or 'Calculating...'}")
            st.write(f"**Estimated Arrival (ETA)**: {incident.get('estimated_arrival_minutes') or 0} mins")

            st.subheader("Outbound Voice Call Alert Status")
            st.write("- **Primary Doctor Call**: :green[Completed (TTS Script sent)]")
            st.write("- **Emergency Contacts Calls**: :green[Completed (TTS Scripts sent)]")

        st.divider()
        st.subheader("Timestamped State Transitions (Audit Trail)")
        st.markdown("Managed by: <span class=\"agent-tag\">Audit Agent (Logging MCP)</span>", unsafe_allow_html=True)
        
        # Build timeline table
        transitions = incident.get("state_transitions", [])
        if not transitions:
            st.write("No transition logs captured.")
        else:
            df = pd.DataFrame(transitions)
            df = df[["status", "notes", "timestamp"]]
            st.table(df)

# ==========================================
# 4. LIVE LOCATION TRACKING
# ==========================================
elif menu == "Live Location Tracking":
    st.markdown('<h1 class="main-title">Ambulance Live Tracking</h1>', unsafe_allow_html=True)
    st.markdown("### Managed by: <span class=\"agent-tag\">Location Agent (Maps MCP)</span>", unsafe_allow_html=True)

    if not st.session_state.active_incident:
        st.info("No active incident to track. Go to Home Dashboard to trigger an alert.")
    else:
        # Sync latest details
        incident = st.session_state.active_incident
        st.write(f"**Dispatched Ambulance**: {incident['assigned_ambulance']}")
        st.write(f"**Assigned Hospital**: {incident['assigned_hospital']}")
        st.write(f"**Current Coordinates**: {incident['latitude']}, {incident['longitude']}")
        st.write(f"**Remaining Travel ETA**: {incident['estimated_arrival_minutes']} mins")

        # Map display (simulated map view)
        map_df = pd.DataFrame({
            "lat": [incident["latitude"]],
            "lon": [incident["longitude"]]
        })
        st.map(map_df, zoom=14)

        st.subheader("Simulate Ambulance Telemetry Updates")
        st.write("Simulate the ambulance moving closer to Mercy General Hospital coordinates (37.7849, -122.4094).")
        
        # Incremental location updater buttons
        col_mv_1, col_mv_2 = st.columns(2)
        with col_mv_1:
            if st.button("Move Ambulance Closer 📍"):
                # Move coordinates slightly closer to hospital (37.7849, -122.4094)
                new_lat = incident["latitude"] + (37.7849 - incident["latitude"]) * 0.4
                new_lon = incident["longitude"] + (-122.4094 - incident["longitude"]) * 0.4
                
                # Send POST /emergency/{incident_id}/location
                res = requests.post(
                    f"{st.session_state.api_url}/emergency/{incident['id']}/location?latitude={new_lat}&longitude={new_lon}"
                )
                if res.status_code == 200:
                    st.session_state.active_incident = res.json()
                    st.success("Ambulance location updated in database!")
                    st.rerun()
                else:
                    st.error("Failed to update coordinates.")
                    
        with col_mv_2:
            if st.button("Ambulance Arrived at Hospital 🏥"):
                res = requests.post(
                    f"{st.session_state.api_url}/emergency/{incident['id']}/location?latitude=37.7849&longitude=-122.4094"
                )
                if res.status_code == 200:
                    st.session_state.active_incident = res.json()
                    st.success("Ambulance arrived at Emergency Department!")
                    st.rerun()
                else:
                    st.error("Failed to register arrival.")

# ==========================================
# 5. INCIDENT HISTORY
# ==========================================
elif menu == "Incident History":
    st.markdown('<h1 class="main-title">Emergency History</h1>', unsafe_allow_html=True)
    st.markdown("### Historical Audit logs of all past telemetry signals.")

    if not st.session_state.patient_id:
        st.info("No patient profile loaded.")
    else:
        try:
            res = requests.get(f"{st.session_state.api_url}/emergency/history?user_id={st.session_state.patient_id}")
            if res.status_code == 200:
                history = res.json()
                if not history:
                    st.info("No past emergency records logged for this user.")
                else:
                    for inc in history:
                        with st.expander(f"Incident: {inc['emergency_type']} ({inc['created_at'][:10]}) - Status: {inc['status']}"):
                            st.write(f"**ID**: {inc['id']}")
                            st.write(f"**Severity**: {inc['severity']}")
                            st.write(f"**Hospital**: {inc['assigned_hospital']}")
                            st.write(f"**Ambulance**: {inc['assigned_ambulance']}")
                            st.subheader("Transitions Timeline")
                            df_trans = pd.DataFrame(inc["state_transitions"])
                            if not df_trans.empty:
                                st.table(df_trans[["status", "notes", "timestamp"]])
            else:
                st.error("Failed to fetch history.")
        except Exception as e:
            st.error(f"Error connecting: {e}")

# ==========================================
# 6. SETTINGS
# ==========================================
elif menu == "Settings":
    st.markdown('<h1 class="main-title">System Settings</h1>', unsafe_allow_html=True)
    
    api_endpoint = st.text_input("FastAPI Endpoint URL", value=st.session_state.api_url)
    if st.button("Save Settings"):
        st.session_state.api_url = api_endpoint
        st.success("Settings updated successfully!")
        st.rerun()
