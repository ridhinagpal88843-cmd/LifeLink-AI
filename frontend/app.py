import streamlit as st
import requests
import time
import pandas as pd
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Setup page layout
st.set_page_config(
    page_title="LifeLink AI - Emergency Operations Center",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern glassmorphism feel
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background-color: #0d0f14;
        color: #e2e8f0;
    }
    
    /* Title & Header */
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff4b4b, #ff7e40);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        padding-bottom: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    
    /* Cards and Glassmorphism */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .status-active {
        color: #10b981;
        font-weight: 600;
    }
    .status-inactive {
        color: #f43f5e;
        font-weight: 600;
    }
    .status-standby {
        color: #94a3b8;
        font-weight: 600;
    }
    
    /* Health Cards Grid */
    .health-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .health-val {
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    
    /* Timeline styles */
    .timeline-wrapper {
        padding-left: 1rem;
        border-left: 2px solid rgba(255, 255, 255, 0.1);
        margin-left: 0.5rem;
        margin-top: 1rem;
    }
    .timeline-node {
        position: relative;
        margin-bottom: 1.2rem;
        padding-left: 1rem;
    }
    .timeline-node::before {
        content: '';
        position: absolute;
        left: -1.45rem;
        top: 0.25rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        box-shadow: 0 0 8px currentColor;
    }
    .timeline-completed {
        color: #10b981;
    }
    .timeline-running {
        color: #3b82f6;
    }
    .timeline-pending {
        color: #64748b;
    }
    .timeline-text {
        font-weight: 500;
        font-size: 0.95rem;
    }
    .timeline-status-badge {
        font-size: 0.75rem;
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.05);
        margin-left: 0.5rem;
    }
    
    /* Agent Grid styles */
    .agent-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    .agent-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        box-shadow: 0 0 6px currentColor;
    }
    .agent-status-tag {
        font-size: 0.8rem;
        font-weight: bold;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
    }
    
    /* Severity Badges */
    .sev-critical {
        background: rgba(244, 63, 94, 0.2);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .sev-high {
        background: rgba(249, 115, 22, 0.2);
        color: #f97316;
        border: 1px solid rgba(249, 115,  orange, 0.3);
    }
    .sev-moderate {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        font-size: 0.85rem;
        color: #64748b;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 2rem;
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
    st.image("https://img.icons8.com/color/96/000000/ambulance.png", width=65)
    st.markdown("## Navigation")
    menu = st.radio(
        "Go to",
        ["Home Dashboard", "Patient Profile", "Emergency Incident", "Live Location Tracking", "Incident History", "Settings"]
    )
    
    st.divider()
    st.markdown("### System Connection")
    backend_connected = False
    try:
        res = requests.get(f"{st.session_state.api_url}/", timeout=1.0)
        if res.status_code == 200:
            st.success("Backend Connected")
            backend_connected = True
        else:
            st.warning("Backend Connected (Degraded)")
            backend_connected = True
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
        logger.error(f"Error seeding patient: {e}")

# Seed patient on startup
if not st.session_state.patient_id and backend_connected:
    auto_seed_patient()

# ==========================================
# 1. HOME DASHBOARD (Emergency Operations Center)
# ==========================================
if menu == "Home Dashboard":
    # 1. Header
    col_header_title, col_header_status = st.columns([8, 4])
    with col_header_title:
        st.markdown('<h1 class="main-title">LifeLink AI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">AI Emergency Healthcare Coordination System</p>', unsafe_allow_html=True)
    
    with col_header_status:
        st.write("")
        status_color = "rgba(16, 185, 129, 0.1)" if backend_connected else "rgba(244, 63, 94, 0.1)"
        status_text = "● ONLINE - SYSTEM GUARD ACTIVE" if backend_connected else "● STANDBY - RE-CONNECTING..."
        status_class = "status-active" if backend_connected else "status-inactive"
        st.markdown(f"""
        <div style="background: {status_color}; border: 1px solid rgba(255,255,255,0.05); padding: 0.75rem 1rem; border-radius: 8px; text-align: right;">
            <span class="{status_class}" style="font-size: 0.9rem; letter-spacing: 0.5px;">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

    # Reload active incident to display current state
    if st.session_state.active_incident and backend_connected:
        try:
            reload_res = requests.get(f"{st.session_state.api_url}/emergency/{st.session_state.active_incident['id']}", timeout=1.0)
            if reload_res.status_code == 200:
                st.session_state.active_incident = reload_res.json()
        except Exception:
            pass

    incident = st.session_state.active_incident

    # Determine status indicators
    workflow_active = incident is not None and incident.get("status") not in ["Resolved", "Closed"]
    current_status = incident.get("status", "Idle") if incident else "Idle"
    current_severity = incident.get("severity", "N/A") if incident else "N/A"
    sev_class = "sev-critical" if current_severity == "Critical" else ("sev-high" if current_severity == "High" else "sev-moderate")
    
    # 2. System Health Cards
    st.markdown("##### System Health & Services")
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns(5)
    with h_col1:
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">AI Agents Status</div>
            <div class="health-val" style="color: #10b981;">● ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">MCP Connections</div>
            <div class="health-val" style="color: #10b981;">● ONLINE</div>
        </div>
        """, unsafe_allow_html=True)
    with h_col3:
        auth_col = "#10b981" if st.session_state.patient_id else "#94a3b8"
        auth_txt = "● SECURED" if st.session_state.patient_id else "● IDLE"
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Authentication</div>
            <div class="health-val" style="color: {auth_col};">{auth_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    with h_col4:
        wf_col = "#f43f5e" if workflow_active else "#94a3b8"
        wf_txt = "● MONITORING" if workflow_active else "● IDLE"
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Workflow Status</div>
            <div class="health-val" style="color: {wf_col};">{wf_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    with h_col5:
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Sensor Stream</div>
            <div class="health-val" style="color: #10b981;">● CONNECTED</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --- Emergency Summary Module ---
    if workflow_active:
        # Fetch patient metadata with robust mock fallback support
        patient_name = "Alexander Pierce"
        patient_age = "35"
        patient_blood = "AB-"
        patient_email = "alexander.pierce@lifelink.ai"
        patient_phone = "+1-555-0811"
        allergies = "Latex, Penicillin"
        conditions = "Type 1 Diabetes, Severe Asthma"
        medications = "Insulin, Albuterol Inhaler"
        primary_doc_name = "Dr. Sarah Connor"
        primary_doc_specialty = "Trauma Care"
        primary_doc_phone = "+1-555-7000"
        emergency_contacts = [
            {"name": "Clara Pierce", "relationship": "Spouse", "phone": "+1-555-1111", "priority": 1},
            {"name": "John Pierce", "relationship": "Brother", "phone": "+1-555-2222", "priority": 2}
        ]
        
        if st.session_state.patient_id and backend_connected:
            try:
                from backend.database import SessionLocal
                from backend.models.user import User
                db = SessionLocal()
                user = db.query(User).filter(User.id == st.session_state.patient_id).first()
                if user:
                    patient_name = user.full_name
                    patient_email = user.email
                    patient_phone = user.phone
                    if user.emergency_health_profile:
                        patient_blood = user.emergency_health_profile.blood_group or "N/A"
                        conditions = user.emergency_health_profile.medical_conditions or "None"
                        allergies = user.emergency_health_profile.allergies or "None"
                        medications = user.emergency_health_profile.current_medications or "None"
                        if user.emergency_health_profile.primary_doctor:
                            primary_doc_name = user.emergency_health_profile.primary_doctor.name
                            primary_doc_specialty = user.emergency_health_profile.primary_doctor.specialty or "General Care"
                            primary_doc_phone = user.emergency_health_profile.primary_doctor.phone
                    if user.emergency_contacts:
                        emergency_contacts = [
                            {
                                "name": c.name,
                                "relationship": c.relationship,
                                "phone": c.phone,
                                "priority": c.priority
                            }
                            for c in user.emergency_contacts
                        ]
                db.close()
            except Exception as e:
                logger.error(f"Error querying patient details: {e}")

        # Render Emergency Summary Card
        st.markdown(f"""
        <div style="border: 2px solid #f43f5e; background: rgba(244, 63, 94, 0.05); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 8px 32px 0 rgba(244, 63, 94, 0.15);">
            <h3 style="color: #f43f5e; margin-top: 0; display: flex; align-items: center; gap: 8px;">🚨 EMERGENCY SUMMARY</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; font-size: 0.95rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 1rem;">
                <div><b>Incident ID:</b> <span style="font-family: monospace;">{incident.get('id', 'N/A')}</span></div>
                <div><b>Detection Timestamp:</b> {incident.get('created_at', 'N/A')}</div>
                <div><b>Emergency Severity:</b> <span class="agent-status-tag {sev_class}" style="display: inline-block;">{current_severity}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_sum_1, col_sum_2 = st.columns(2)
        with col_sum_1:
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h5 style="margin-top: 0; color: #f43f5e;">👤 Patient Information</h5>
                <p style="font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.6;">
                    <b>Patient Name:</b> {patient_name}<br/>
                    <b>Age:</b> {patient_age} years<br/>
                    <b>Blood Group:</b> {patient_blood}<br/>
                    <b>Emergency ID:</b> <code>{st.session_state.patient_id}</code>
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h5 style="margin-top: 0; color: #f43f5e;">❤️ Medical Information</h5>
                <p style="font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.6;">
                    <b>Known Allergies:</b> {allergies}<br/>
                    <b>Existing Medical Conditions:</b> {conditions}<br/>
                    <b>Current Medications:</b> {medications}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_sum_2:
            doc_notified = "✓ Notified" if current_status in ["Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"] else "Pending"
            doc_color = "#10b981" if doc_notified == "✓ Notified" else "#eab308"
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h5 style="margin-top: 0; color: #f43f5e;">👨‍⚕️ Healthcare Coordination</h5>
                <p style="font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.6;">
                    <b>Primary Doctor:</b> {primary_doc_name} ({primary_doc_specialty})<br/>
                    <b>Doctor Notification Status:</b> <span style="color: {doc_color}; font-weight: bold;">{doc_notified}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Build list of Top 5 contacts
            padded_contacts = list(emergency_contacts)
            while len(padded_contacts) < 5:
                padded_contacts.append(None)
                
            contacts_html = ""
            for idx, contact in enumerate(padded_contacts):
                if contact:
                    if current_status in ["Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]:
                        notif_status = "✓ Notified"
                        badge_color = "#10b981"
                    elif current_status == "Doctor Contacted" and contact["priority"] == 1:
                        notif_status = "✓ Notified"
                        badge_color = "#10b981"
                    else:
                        notif_status = "Pending"
                        badge_color = "#94a3b8"
                    contacts_html += f"<li><b>{contact['name']}</b> ({contact['relationship']}): {contact['phone']} — <span style='color: {badge_color}; font-weight: bold;'>{notif_status}</span></li>"
                else:
                    contacts_html += f"<li><i>Not Configured</i></li>"
                    
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h5 style="margin-top: 0; color: #f43f5e;">👨‍👩‍👧 Emergency Contacts</h5>
                <ul style="font-size: 0.95rem; margin-bottom: 0.5rem; padding-left: 1.2rem; list-style-type: decimal; line-height: 1.6;">
                    {contacts_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # Location, AI Summary, and checklist
        gps_loc = f"{incident.get('latitude', 37.7749)}, {incident.get('longitude', -122.4194)}"
        last_updated = incident.get("updated_at", "N/A")
        
        # Calculate checklist completion
        classified = current_status not in ["Detected"]
        doctor_alert = current_status in ["Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]
        family_alert = current_status in ["Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]
        services_initiated = current_status in ["Ambulance En Route", "Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]
        logged = current_status in ["Resolved", "Closed", "Hospital Admission"]
        
        check_sensor = "🟢 ✓ Sensor Alert Received"
        check_classified = "🟢 ✓ Emergency Classified" if classified else "⚪ Emergency Classified"
        check_doctor = "🟢 ✓ Doctor Notified" if doctor_alert else "⚪ Doctor Notified"
        check_family = "🟢 ✓ Family Alerted" if family_alert else "⚪ Family Alerted"
        check_services = "🟢 ✓ Emergency Services Initiated" if services_initiated else "⚪ Emergency Services Initiated"
        check_logged = "🟢 ✓ Incident Logged" if logged else "⚪ Incident Logged"

        st.markdown(f"""
        <div style="border: 1px solid rgba(255,255,255,0.08); background: rgba(30, 41, 59, 0.45); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div>
                    <h5 style="margin-top: 0; color: #3b82f6;">📍 Location</h5>
                    <p style="font-size: 0.95rem; margin-bottom: 1rem; line-height: 1.6;">
                        <b>Current GPS Coordinates:</b> <code>{gps_loc}</code><br/>
                        <b>Last Updated:</b> {last_updated}
                    </p>
                    <h5 style="margin-top: 0; color: #3b82f6;">🤖 AI Decision Summary</h5>
                    <p style="font-size: 0.95rem; font-style: italic; color: #cbd5e1; line-height: 1.5;">
                        "LifeLink AI detected abnormal sensor readings indicating a high-risk emergency. Based on the patient's emergency profile, the AI initiated emergency coordination, notified the primary doctor, alerted emergency contacts, and activated emergency services."
                    </p>
                </div>
                <div>
                    <h5 style="margin-top: 0; color: #10b981;">🚑 Response Status</h5>
                    <div style="display: grid; grid-template-columns: 1fr; gap: 0.5rem; font-size: 0.95rem; font-weight: 500;">
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: rgba(16, 185, 129, 0.1); color: #10b981;">{check_sensor}</div>
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: {'rgba(16, 185, 129, 0.1)' if classified else 'rgba(255,255,255,0.02)'}; color: {'#10b981' if classified else '#94a3b8'};">{check_classified}</div>
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: {'rgba(16, 185, 129, 0.1)' if doctor_alert else 'rgba(255,255,255,0.02)'}; color: {'#10b981' if doctor_alert else '#94a3b8'};">{check_doctor}</div>
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: {'rgba(16, 185, 129, 0.1)' if family_alert else 'rgba(255,255,255,0.02)'}; color: {'#10b981' if family_alert else '#94a3b8'};">{check_family}</div>
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: {'rgba(16, 185, 129, 0.1)' if services_initiated else 'rgba(255,255,255,0.02)'}; color: {'#10b981' if services_initiated else '#94a3b8'};">{check_services}</div>
                        <div style="padding: 0.3rem 0.6rem; border-radius: 4px; background: {'rgba(16, 185, 129, 0.1)' if logged else 'rgba(255,255,255,0.02)'}; color: {'#10b981' if logged else '#94a3b8'};">{check_logged}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Primary Content Section
    col_main_left, col_main_right = st.columns([7, 5])
    
    with col_main_left:
        # 3. Emergency Monitoring Panel
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🚨 Emergency Monitoring Panel")
        
        # Already loaded globally
        
        # Map active agent
        if current_status == "Idle":
            active_agent = "Standby"
            stage = "Monitoring Device Streams"
        elif current_status == "Detected":
            active_agent = "Sensor / Medical Profile Agent"
            stage = "Triage Evaluation"
        elif current_status == "Dispatching":
            active_agent = "Emergency Coordinator Agent"
            stage = "Resource Dispatching"
        elif current_status == "Ambulance En Route":
            active_agent = "Location Routing Agent"
            stage = "Ambulance Transit"
        elif current_status == "Doctor Contacted":
            active_agent = "Doctor Coordination Agent"
            stage = "Physician Alert"
        elif current_status == "Family Contacted":
            active_agent = "Family Notification Agent"
            stage = "Family Contact Voice calls"
        elif current_status == "Patient Reached":
            active_agent = "Location Agent"
            stage = "On-site Medical Treatment"
        elif current_status == "Hospital Admission":
            active_agent = "Emergency Services Agent"
            stage = "Hospital Intake"
        elif current_status in ["Resolved", "Closed"]:
            active_agent = "Audit Agent"
            stage = "Audit Complete"
        else:
            active_agent = "Emergency Coordinator Agent"
            stage = "Processing Telemetry"

        sev_class = "sev-critical" if current_severity == "Critical" else ("sev-high" if current_severity == "High" else "sev-moderate")
        if current_severity == "N/A":
            sev_class = "style='color: #64748b; background: rgba(255,255,255,0.03); padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: bold;'"
        else:
            sev_class = f"class='agent-status-tag {sev_class}'"

        mon_col1, mon_col2 = st.columns(2)
        with mon_col1:
            st.markdown(f"**Emergency Level**: <span {sev_class}>{current_severity}</span>", unsafe_allow_html=True)
            st.markdown(f"**Current Incident Status**: :red[{current_status}]")
            st.markdown(f"**Current Active AI Agent**: `{active_agent}`")
        with mon_col2:
            st.markdown(f"**Current Workflow Stage**: `{stage}`")
            st.markdown(f"**Live Timestamp**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

        # Display vitals if incident is active
        if incident:
            st.divider()
            st.markdown("##### Real-Time Ingested Telemetry Vitals")
            v_col1, v_col2, v_col3 = st.columns(3)
            # Extrapolate mock vitals based on emergency type
            spo2 = 88 if "Asthma" in incident["emergency_type"] else 98
            hr = 125 if "Cardiac" in incident["emergency_type"] or "Asthma" in incident["emergency_type"] else 76
            with v_col1:
                st.metric("SpO2 Level", f"{spo2}%", delta="-10%" if spo2 < 90 else None, delta_color="inverse")
            with v_col2:
                st.metric("Heart Rate", f"{hr} bpm", delta="+45 bpm" if hr > 100 else None, delta_color="inverse")
            with v_col3:
                st.metric("Respiratory Rate", "24/min" if hr > 100 else "14/min")
                
        st.markdown('</div>', unsafe_allow_html=True)

        # 5. Live Workflow Timeline
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ⏳ Live Workflow Timeline")
        
        stages = [
            ("Sensor Detection", ["Detected", "Dispatching", "Ambulance En Route", "Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Emergency Coordinator", ["Dispatching", "Ambulance En Route", "Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Medical Profile Retrieval", ["Dispatching", "Ambulance En Route", "Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Emergency Summary Generation", ["Ambulance En Route", "Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Doctor Notification", ["Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Family Notification", ["Family Contacted", "Patient Reached", "Hospital Admission", "Resolved"]),
            ("Emergency Services Coordination", ["Patient Reached", "Hospital Admission", "Resolved"]),
            ("Incident Logging", ["Resolved"])
        ]
        
        st.markdown('<div class="timeline-wrapper">', unsafe_allow_html=True)
        for stage_name, completion_statuses in stages:
            if not incident:
                state = "Pending"
            elif incident.get("status") in completion_statuses:
                state = "Completed"
            elif incident.get("status") == "Detected" and stage_name in ["Sensor Detection"]:
                state = "Completed"
            elif incident.get("status") == "Detected" and stage_name in ["Emergency Coordinator"]:
                state = "Running"
            elif incident.get("status") == "Dispatching" and stage_name in ["Medical Profile Retrieval", "Emergency Summary Generation"]:
                state = "Running"
            elif incident.get("status") in ["Ambulance En Route", "Doctor Contacted", "Family Contacted"] and stage_name in ["Doctor Notification", "Family Notification", "Emergency Services Coordination"]:
                state = "Running"
            elif incident.get("status") == "Hospital Admission" and stage_name == "Incident Logging":
                state = "Running"
            else:
                state = "Pending"
                
            color_class = "timeline-completed" if state == "Completed" else ("timeline-running" if state == "Running" else "timeline-pending")
            badge_color = "background: rgba(16, 185, 129, 0.2); color: #10b981;" if state == "Completed" else ("background: rgba(59, 130, 246, 0.2); color: #3b82f6;" if state == "Running" else "background: rgba(100, 116, 139, 0.2); color: #94a3b8;")
            
            st.markdown(f"""
            <div class="timeline-node {color_class}">
                <span class="timeline-text">{stage_name}</span>
                <span class="timeline-status-badge" style="{badge_color}">{state.upper()}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Trigger Simulation Section (Helper inside EOC)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Simulation Control Unit")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            sim_emergency_type = st.selectbox(
                "Trigger Vitals Alarm Condition",
                ["Cardiac Arrest", "Asthma Attack", "Severe Facial Droop & Speech Loss", "Anxiety & Palpitations"],
                key="eoc_sim_type"
            )
            sim_latitude = st.number_input("Patient Lat", value=37.7749, format="%.4f", key="eoc_sim_lat")
        with col_ctrl2:
            sim_severity = st.selectbox("Trigger Severity", ["Critical", "High", "Moderate"], key="eoc_sim_sev")
            sim_longitude = st.number_input("Patient Lon", value=-122.4194, format="%.4f", key="eoc_sim_lon")
        
        trigger_btn = st.button("TRIGGER TELEMETRY ALERT 🚨", use_container_width=True, key="eoc_trigger_btn")
        if trigger_btn:
            if not st.session_state.patient_id:
                st.error("Error: No Patient ID seeded. Auto-seed profile before triggering.")
            else:
                with st.spinner("Executing Google ADK pipeline..."):
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
                        st.success("Emergency logged! Multi-agent pipeline initialized.")
                        st.rerun()
                    else:
                        st.error(f"Execution failed: {res.text}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_main_right:
        # 6. Patient Summary Panel
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 Patient Summary Panel")
        
        # Load Patient Details
        patient_name = "Alexander Pierce"
        patient_age = "45"
        patient_blood = "AB-"
        primary_doc = "Dr. Sarah Connor"
        family_contacts_html = """
        <li><b>Clara Pierce</b> (Spouse): +1-555-1111 [Priority 1]</li>
        <li><b>John Pierce</b> (Brother): +1-555-2222 [Priority 2]</li>
        """
        
        if st.session_state.patient_id and backend_connected:
            try:
                from backend.database import SessionLocal
                from backend.models.user import User
                db = SessionLocal()
                user = db.query(User).filter(User.id == st.session_state.patient_id).first()
                if user:
                    patient_name = user.full_name
                    patient_blood = user.emergency_health_profile.blood_group
                    primary_doc = user.emergency_health_profile.primary_doctor.name if user.emergency_health_profile.primary_doctor else "N/A"
                    family_contacts_html = ""
                    for c in user.emergency_contacts:
                        family_contacts_html += f"<li><b>{c.name}</b> ({c.relationship}): {c.phone} [Priority {c.priority}]</li>"
                db.close()
            except Exception:
                pass
                
        st.markdown(f"""
        <div style="font-size: 0.95rem; line-height: 1.6;">
            <div><b>Patient Name</b>: {patient_name}</div>
            <div><b>Age</b>: {patient_age} years</div>
            <div><b>Blood Group</b>: <span style="background: rgba(244,63,94,0.15); color: #f43f5e; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: bold;">{patient_blood}</span></div>
            <div><b>Primary Doctor</b>: {primary_doc}</div>
            <div style="margin-top: 0.5rem; margin-bottom: 0.2rem;"><b>Emergency Contacts</b>:</div>
            <ul style="margin: 0; padding-left: 1.2rem;">
                {family_contacts_html}
            </ul>
            <hr style="margin: 0.8rem 0; border: 0; border-top: 1px solid rgba(255,255,255,0.05);" />
            <div><b>Current Emergency Level</b>: <span style="color: #f43f5e; font-weight: bold;">{current_severity}</span></div>
            <div><b>Current Status</b>: <span style="color: #3b82f6; font-weight: bold;">{current_status}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 7. Incident Status Panel
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📋 Incident Status Panel")
        
        inc_id = incident.get("id", "N/A") if incident else "N/A"
        inc_time = incident.get("created_at", "N/A") if incident else "N/A"
        inc_loc = f"{incident.get('latitude', 37.7749)}, {incident.get('longitude', -122.4194)}" if incident else "N/A"
        
        # Geocode simulated address if coordinates exist
        if incident:
            inc_loc = "1230 Market St, San Francisco, CA"
            
        ambulance_status = "Standby"
        doctor_status = "Standby"
        family_status = "Standby"
        
        if incident:
            if current_status in ["Ambulance En Route", "Doctor Contacted", "Family Contacted"]:
                ambulance_status = f"En Route ({incident.get('assigned_ambulance') or 'Ambulance #4'})"
            elif current_status in ["Patient Reached", "Hospital Admission"]:
                ambulance_status = "Arrived at Hospital"
            elif current_status in ["Resolved", "Closed"]:
                ambulance_status = "Completed"
            else:
                ambulance_status = "Dispatched"
                
            if current_status in ["Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]:
                doctor_status = "Notified (Clinical Alert TTS)"
            else:
                doctor_status = "Queued for calling"
                
            if current_status in ["Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"]:
                family_status = "Notified (Contact Voice Alerts)"
            else:
                family_status = "Queued for calling"

        st.markdown(f"""
        <div style="font-size: 0.95rem; line-height: 1.6;">
            <div><b>Incident ID</b>: <span style="font-family: monospace; font-size: 0.85rem;">{inc_id}</span></div>
            <div><b>Detection Time</b>: {inc_time}</div>
            <div><b>Current Location</b>: {inc_loc}</div>
            <hr style="margin: 0.8rem 0; border: 0; border-top: 1px solid rgba(255,255,255,0.05);" />
            <div><b>Ambulance Status</b>: <span style="color: #3b82f6; font-weight: 500;">{ambulance_status}</span></div>
            <div><b>Doctor Status</b>: <span style="color: #10b981; font-weight: 500;">{doctor_status}</span></div>
            <div><b>Family Status</b>: <span style="color: #10b981; font-weight: 500;">{family_status}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. AI Agent Coordination Panel
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🤖 AI Agent Coordination Panel")
        
        agents_list = [
            ("Sensor Agent", "Ingests vital signals & maps telemetry streams", "Detected" if incident else "Standby"),
            ("Emergency Coordinator Agent", "Orchestrates multi-agent pipeline workflow & handles dispatch", "Active" if current_status == "Dispatching" else ("Completed" if incident else "Standby")),
            ("Medical Profile Agent", "Retrieves patient clinical profile details via Patient DB", "Completed" if incident else "Standby"),
            ("Emergency Summary Agent", "Performs triage assessment & formats clinical alerts", "Completed" if incident else "Standby"),
            ("Doctor Coordination Agent", "Initiates secure TTS outbound voice calls to physician", "Completed" if current_status in ["Doctor Contacted", "Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"] else ("Active" if current_status in ["Dispatching", "Ambulance En Route"] else "Standby")),
            ("Family Notification Agent", "Initiates prioritized contact alerts to emergency profile contacts", "Completed" if current_status in ["Family Contacted", "Patient Reached", "Hospital Admission", "Resolved", "Closed"] else ("Active" if current_status in ["Doctor Contacted"] else "Standby")),
            ("Emergency Services Agent", "Manages hospital intake & final resource handoff procedures", "Completed" if current_status in ["Patient Reached", "Hospital Admission", "Resolved", "Closed"] else ("Active" if current_status in ["Ambulance En Route"] else "Standby")),
            ("Audit Agent", "Logs timestamps & timeline transitions in the Logging MCP", "Completed" if current_status in ["Resolved", "Closed"] else ("Active" if current_status in ["Hospital Admission"] else "Standby"))
        ]
        
        for name, role, state in agents_list:
            if state == "Completed":
                dot_color = "#10b981"
                bg_color = "rgba(16, 185, 129, 0.15)"
                text_color = "#10b981"
            elif state == "Active":
                dot_color = "#3b82f6"
                bg_color = "rgba(59, 130, 246, 0.15)"
                text_color = "#3b82f6"
            else:
                dot_color = "#64748b"
                bg_color = "rgba(100, 116, 139, 0.15)"
                text_color = "#94a3b8"
                
            st.markdown(f"""
            <div class="agent-row">
                <div>
                    <span class="agent-dot" style="color: {dot_color};"></span>
                    <span style="font-weight: 600; font-size: 0.9rem;">{name}</span>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-left: 14px;">{role}</div>
                </div>
                <span class="agent-status-tag" style="background: {bg_color}; color: {text_color};">{state.upper()}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 8. Footer
    st.markdown('<div class="footer">Powered by Google Agent Development Kit (ADK) + Model Context Protocol (MCP)</div>', unsafe_allow_html=True)

# ==========================================
# 2. PATIENT PROFILE
# ==========================================
elif menu == "Patient Profile":
    st.markdown('<h1 class="main-title">Patient Profile & Clinical History</h1>', unsafe_allow_html=True)
    st.markdown("### Managed by: <span class=\"agent-tag\">Medical Profile Agent</span>", unsafe_allow_html=True)

    if not st.session_state.patient_id and backend_connected:
        st.warning("No Patient profile loaded. Auto-seeding a default patient profile in the backend database...")
        auto_seed_patient()

    # Load Patient Profile from DB directly
    try:
        from backend.database import SessionLocal
        from backend.models.user import User
        db = SessionLocal()
        user = db.query(User).filter(User.id == st.session_state.patient_id).first()
        
        if user:
            col_profile_1, col_profile_2 = st.columns(2)
            with col_profile_1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Personal Information")
                st.write(f"**Full Name**: {user.full_name}")
                st.write(f"**Email**: {user.email}")
                st.write(f"**Phone**: {user.phone}")
                st.write(f"**Patient ID (UUID)**: {user.id}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Primary Physician")
                doctor = user.emergency_health_profile.primary_doctor
                if doctor:
                    st.write(f"**Doctor Name**: {doctor.name}")
                    st.write(f"**Specialty**: {doctor.specialty}")
                    st.write(f"**Phone**: {doctor.phone}")
                    st.write(f"**Email**: {doctor.email}")
                else:
                    st.write("No primary physician registered.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_profile_2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Emergency Health Profile")
                profile = user.emergency_health_profile
                st.write(f"**Blood Group**: {profile.blood_group}")
                st.write(f"**Existing Conditions**: {profile.medical_conditions}")
                st.write(f"**Allergies**: {profile.allergies}")
                st.write(f"**Current Medications**: {profile.current_medications}")
                st.write(f"**Emergency Preferences**: {profile.emergency_preferences}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Emergency Contacts (Top 5)")
                for contact in user.emergency_contacts:
                    st.write(f"- **{contact.name}** ({contact.relationship}): {contact.phone} [Priority {contact.priority}]")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("No Patient profile found. Verify backend database setup.")
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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Incident Vitals")
            st.write(f"**Incident ID (UUID)**: {incident['id']}")
            st.write(f"**Reported Emergency**: {incident['emergency_type']}")
            st.write(f"**Assigned Severity**: {incident['severity']}")
            st.write(f"**Current Lifecycle Status**: :red[{incident['status']}]")
            st.write(f"**Latitude/Longitude**: {incident['latitude']}, {incident['longitude']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("AI Agent Decision Logs")
            if incident.get("agent_decision_log"):
                decision_log = json.loads(incident["agent_decision_log"])
                st.json(decision_log)
            else:
                st.write("No agent decision logs posted yet.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_inc_2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Dispatch Details")
            st.write(f"**Assigned Hospital**: {incident.get('assigned_hospital') or 'Calculating...'}")
            st.write(f"**Dispatched Ambulance**: {incident.get('assigned_ambulance') or 'Calculating...'}")
            st.write(f"**Estimated Arrival (ETA)**: {incident.get('estimated_arrival_minutes') or 0} mins")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Outbound Voice Call Alert Status")
            st.write("- **Primary Doctor Call**: :green[Completed (TTS Script sent)]")
            st.write("- **Emergency Contacts Calls**: :green[Completed (TTS Scripts sent)]")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

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
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write(f"**Dispatched Ambulance**: {incident['assigned_ambulance']}")
        st.write(f"**Assigned Hospital**: {incident['assigned_hospital']}")
        st.write(f"**Current Coordinates**: {incident['latitude']}, {incident['longitude']}")
        st.write(f"**Remaining Travel ETA**: {incident['estimated_arrival_minutes']} mins")
        st.markdown('</div>', unsafe_allow_html=True)

        # Map display (simulated map view)
        map_df = pd.DataFrame({
            "lat": [incident["latitude"]],
            "lon": [incident["longitude"]]
        })
        st.map(map_df, zoom=14)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

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
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    api_endpoint = st.text_input("FastAPI Endpoint URL", value=st.session_state.api_url)
    if st.button("Save Settings"):
        st.session_state.api_url = api_endpoint
        st.success("Settings updated successfully!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
