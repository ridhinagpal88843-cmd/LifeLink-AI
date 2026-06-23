from backend.agents.triage_agent import TriageAgent, TriageResult


def test_heart_attack_classification():
    """
    Test TriageAgent detects heart attack correctly from chest pain and high heart rate.
    """
    agent = TriageAgent()
    vitals = {"heart_rate": 125, "spo2": 97}
    symptoms = ["Chest Pain", "Shortness of breath", "Sweating"]
    history = {"medical_conditions": "Hypertension"}
    
    result = agent.triage(vitals, symptoms, history)
    
    assert isinstance(result, TriageResult)
    assert result.emergency_type == "Heart Attack"
    assert result.severity == "Critical"
    assert result.confidence_score > 0.8
    assert "aspirin" in result.emergency_protocol.lower()


def test_asthma_attack_classification():
    """
    Test TriageAgent detects asthma attack from wheezing, low oxygen levels, and history.
    """
    agent = TriageAgent()
    vitals = {"heart_rate": 95, "spo2": 89}
    symptoms = ["Wheezing", "Shortness of breath"]
    history = {"medical_conditions": "Mild Asthma"}
    
    result = agent.triage(vitals, symptoms, history)
    
    assert result.emergency_type == "Asthma Attack"
    assert result.severity == "High"
    assert "inhaler" in result.emergency_protocol.lower()


def test_stroke_classification():
    """
    Test TriageAgent detects stroke from neurological symptoms.
    """
    agent = TriageAgent()
    vitals = {"heart_rate": 78, "spo2": 98}
    symptoms = ["Facial droop", "Slurred speech"]
    history = {}
    
    result = agent.triage(vitals, symptoms, history)
    
    assert result.emergency_type == "Stroke"
    assert result.severity == "Critical"
    assert "FAST" in result.emergency_protocol


def test_panic_attack_classification():
    """
    Test TriageAgent detects panic attack under normal SpO2 and high anxiety indicators.
    """
    agent = TriageAgent()
    vitals = {"heart_rate": 115, "spo2": 97}
    symptoms = ["Anxiety", "Panic", "Palpitations"]
    history = {}
    
    result = agent.triage(vitals, symptoms, history)
    
    assert result.emergency_type == "Panic Attack"
    assert result.severity == "Moderate"
    assert "breathing" in result.emergency_protocol.lower()


def test_unknown_vitals_classification():
    """
    Test TriageAgent defaults to Unknown when vitals and symptoms do not match protocols.
    """
    agent = TriageAgent()
    vitals = {"heart_rate": 72, "spo2": 98}
    symptoms = ["Sore throat", "Cough"]
    history = {}
    
    result = agent.triage(vitals, symptoms, history)
    
    assert result.emergency_type == "Unknown"
    assert result.severity == "Moderate"
