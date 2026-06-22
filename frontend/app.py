import streamlit as st
import time
import requests
import random

# Page Configuration for modern premium feel
st.set_page_config(
    page_title="LifeLink AI - Emergency Coordination Dashboard",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stylized Custom CSS for modern glassmorphism UI
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main-title {
        font-size: 3rem;
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
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Settings and simulator triggers
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/ambulance.png", width=80)
    st.markdown("## Control Center")
    st.markdown("Simulate emergency telemetry feeds to trigger LifeLink AI multi-agent orchestrator workflow.")
    
    severity_level = st.selectbox(
        "Simulate Sensor Vitals Alert",
        ["Critical (Cardiac Arrest)", "High (Severe Trauma)", "Moderate (Difficulty Breathing)", "Low (Minor Injury)"]
    )
    
    patient_id = st.text_input("Simulate Patient ID", "PATIENT-9082")
    
    trigger_btn = st.button("Trigger Emergency Telemetry 🚨", use_container_width=True)

# Main Application Layout
st.markdown('<h1 class="main-title">LifeLink AI Coordination Panel</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Emergency Healthcare Orchestrator & Sensor Telemetry Feed")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="metric-card">
            <h3 style='margin:0;color:#ff4b4b;'>Active Incidents</h3>
            <h1 style='margin:0;color:white;'>0</h1>
            <p style='margin:0;color:#888;'>Pending dispatch action</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="metric-card" style="border-left: 5px solid #00c853;">
            <h3 style='margin:0;color:#00c853;'>Available Ambulances</h3>
            <h1 style='margin:0;color:white;'>12</h1>
            <p style='margin:0;color:#888;'>GPS tracked & online</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="metric-card" style="border-left: 5px solid #2979ff;">
            <h3 style='margin:0;color:#2979ff;'>Hospital Bed Capacity</h3>
            <h1 style='margin:0;color:white;'>45</h1>
            <p style='margin:0;color:#888;'>ICU / Emergency Beds</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.divider()

if trigger_btn:
    st.subheader(f"Processing Event: {severity_level} (Patient: {patient_id})")
    
    # Visual simulation sequence of the Agent Workflow
    with st.status("Initializing AI Multi-Agent Coordination...", expanded=True) as status:
        st.write("📥 Telemetry ingested from wearable smartwatch sensor...")
        time.sleep(0.8)
        
        st.write("🧠 **TriageAgent** assessing patient vitals (Heart Rate: 135 bpm, SpO2: 88%)...")
        time.sleep(1.0)
        
        st.write("🏥 **ResourceAllocationAgent** querying MCP tools for closest ICU beds...")
        time.sleep(1.2)
        
        st.write("🚑 **DispatcherAgent** calculating traffic routing & dispatching Ambulance #4...")
        time.sleep(1.0)
        
        status.update(label="Incident Dispatched Successfully! (Response Time Reduced by 34%)", state="complete")
        
    st.balloons()
    
    st.success("LifeLink AI completed routing. Ambulance #4 dispatched to Mercy General Hospital (ETA: 7 mins).")
else:
    st.info("Select vitals on the sidebar and click **Trigger Emergency Telemetry** to simulate the AI Orchestration flow.")
