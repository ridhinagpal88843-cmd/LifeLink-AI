from backend.services.voice_service import VoiceCallEngine


def test_doctor_voice_script_generation():
    """
    Test that doctor scripts compile clinical patient history.
    """
    script = VoiceCallEngine.generate_doctor_script(
        patient_name="John Doe",
        emergency_type="Cardiac Arrest",
        severity="Critical",
        location="123 Main St",
        medical_conditions="Diabetes, Asthma",
        allergies="Peanuts",
        assigned_hospital="Mercy Hospital",
        eta=10
    )
    
    assert "John Doe" in script
    assert "Cardiac Arrest" in script
    assert "Diabetes, Asthma" in script
    assert "Peanuts" in script
    assert "Mercy Hospital" in script
    assert "10 minutes" in script
    assert "Your patient" in script


def test_contact_voice_script_generation():
    """
    Test that family member scripts provide supportive instructions.
    """
    script = VoiceCallEngine.generate_contact_script(
        patient_name="John Doe",
        relationship="Spouse",
        emergency_type="Respiratory Distress",
        location="123 Main St",
        assigned_hospital="City General",
        eta=8
    )

    assert "John Doe" in script
    assert "Respiratory Distress" in script
    assert "City General" in script
    assert "8 minutes" in script
    assert "emergency contact" in script
    assert "Urgent notification" in script
