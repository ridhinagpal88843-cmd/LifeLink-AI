import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.config import settings
# Import Google GenAI SDK (imported safely)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class TriageResult(BaseModel):
    """
    Structured output schema for the Triage Agent's assessment.
    """
    emergency_type: str = Field(..., description="Probable emergency type: Heart Attack, Stroke, Asthma Attack, Panic Attack, or Unknown")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    severity: str = Field(..., description="Severity level: Critical, High, Moderate, Low")
    emergency_protocol: str = Field(..., description="Immediate clinical / first-aid instructions")
    triage_summary: str = Field(..., description="Cohesive overview of vitals, medical history matches, and triage rationale")


class TriageConditionRule:
    """
    Base class for modular, extensible diagnostic fallback rules.
    Additional rules can be registered to scale the offline system.
    """
    def matches(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def evaluate(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        raise NotImplementedError


# --- Modular Fallback Rules ---

class HeartAttackRule(TriageConditionRule):
    def matches(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> bool:
        symptom_set = {s.lower() for s in symptoms}
        has_chest_pain = "chest pain" in symptom_set or "pressure" in symptom_set
        has_arm_pain = "left arm pain" in symptom_set or "left shoulder pain" in symptom_set
        hr = vitals.get("heart_rate", 80)
        
        # Matches chest pain + high heart rate, or chest pain + left arm pain, or history of heart disease + symptoms
        history_str = history.get("medical_conditions", "").lower()
        has_cardiac_history = "heart" in history_str or "coronary" in history_str or "cardio" in history_str
        
        return (has_chest_pain and (hr > 110 or has_arm_pain)) or (has_chest_pain and has_cardiac_history)

    def evaluate(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        return TriageResult(
            emergency_type="Heart Attack",
            confidence_score=0.92,
            severity="Critical",
            emergency_protocol="Administer aspirin if patient is not allergic. Keep patient sitting and calm. Prepare AED.",
            triage_summary=(
                f"Cardiac event flagged. Symptoms include chest pain and high heart rate ({vitals.get('heart_rate')} bpm). "
                f"Medical history shows: {history.get('medical_conditions', 'none')}. High risk of coronary blockage."
            )
        )


class AsthmaAttackRule(TriageConditionRule):
    def matches(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> bool:
        symptom_set = {s.lower() for s in symptoms}
        wheezing = "wheezing" in symptom_set or "shortness of breath" in symptom_set or "difficulty breathing" in symptom_set
        spo2 = vitals.get("spo2", 98)
        history_str = history.get("medical_conditions", "").lower()
        has_asthma_history = "asthma" in history_str or "copd" in history_str
        
        return wheezing and (spo2 < 92 or has_asthma_history)

    def evaluate(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        return TriageResult(
            emergency_type="Asthma Attack",
            confidence_score=0.88,
            severity="High",
            emergency_protocol="Administer rescue inhaler (albuterol). Sit patient upright. Administer oxygen if SpO2 below 90%.",
            triage_summary=(
                f"Respiratory distress flagged. Low SpO2 level detected ({vitals.get('spo2')}%). "
                f"Medical history includes: {history.get('medical_conditions', 'none')}."
            )
        )


class StrokeRule(TriageConditionRule):
    def matches(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> bool:
        symptom_set = {s.lower() for s in symptoms}
        stroke_symptoms = {"slurred speech", "facial droop", "arm weakness", "numbness", "confusion"}
        return len(symptom_set.intersection(stroke_symptoms)) >= 2

    def evaluate(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        return TriageResult(
            emergency_type="Stroke",
            confidence_score=0.95,
            severity="Critical",
            emergency_protocol="Perform FAST assessment. Record time of symptom onset. Keep patient lying down. Do not give food or drink.",
            triage_summary="Neurological deficits identified matching stroke criteria (FAST symptoms present). Time critical intervention needed."
        )


class PanicAttackRule(TriageConditionRule):
    def matches(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> bool:
        symptom_set = {s.lower() for s in symptoms}
        anxiety = "panic" in symptom_set or "hyperventilation" in symptom_set or "anxiety" in symptom_set
        hr = vitals.get("heart_rate", 80)
        spo2 = vitals.get("spo2", 98)
        return anxiety and hr > 100 and spo2 >= 95

    def evaluate(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        return TriageResult(
            emergency_type="Panic Attack",
            confidence_score=0.80,
            severity="Moderate",
            emergency_protocol="Coached breathing exercises. Reassurance. Move to a quiet environment.",
            triage_summary=f"Elevated heart rate ({vitals.get('heart_rate')} bpm) with normal SpO2 ({vitals.get('spo2')}%). Patient exhibits anxiety and panic signs."
        )


# --- Triage Agent Core ---

class TriageAgent:
    """
    AI Triage Agent analyzing vitals telemetry, symptoms, and medical profiles.
    Modular fallback rules allow validation and testing without Gemini API key configurations.
    """

    def __init__(self):
        # Register fallback rules (Order matters)
        self.rules: List[TriageConditionRule] = [
            HeartAttackRule(),
            StrokeRule(),
            AsthmaAttackRule(),
            PanicAttackRule()
        ]
        
        # Configure Gemini Client if key exists
        self.client = None
        if GENAI_AVAILABLE and settings.GOOGLE_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}")

    def triage(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        """
        Executes triage assessment. Prefers Gemini AI if online, otherwise triggers modular rules engine.
        """
        if self.client:
            try:
                return self._triage_via_ai(vitals, symptoms, history)
            except Exception as e:
                logger.error(f"Gemini Triage failed, falling back to rule engine: {e}")
                return self._triage_via_rules(vitals, symptoms, history)
        else:
            return self._triage_via_rules(vitals, symptoms, history)

    def _triage_via_rules(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        """
        Executes rule-based matching.
        """
        for rule in self.rules:
            if rule.matches(vitals, symptoms, history):
                return rule.evaluate(vitals, symptoms, history)
        
        # Fallback unknown category
        return TriageResult(
            emergency_type="Unknown",
            confidence_score=0.50,
            severity="High" if vitals.get("heart_rate", 80) > 120 or vitals.get("spo2", 98) < 90 else "Moderate",
            emergency_protocol="Monitor vitals. Keep patient resting. Alert nearest medical unit.",
            triage_summary="Vitals and symptoms do not match specific primary protocols. Telemetry shows abnormal signals."
        )

    def _triage_via_ai(self, vitals: Dict[str, Any], symptoms: List[str], history: Dict[str, Any]) -> TriageResult:
        """
        Executes AI triage calling Gemini-2.5-Flash with strict Pydantic schema constraints.
        """
        prompt = (
            f"You are the LifeLink AI Emergency Triage Agent.\n"
            f"Analyze the following patient data and categorize the emergency.\n\n"
            f"Patient Vitals Telemetry:\n{json.dumps(vitals, indent=2)}\n\n"
            f"Reported Symptoms:\n{', '.join(symptoms)}\n\n"
            f"Patient Medical History Snapshot:\n{json.dumps(history, indent=2)}\n\n"
            f"Categorize the most probable emergency type as either: Heart Attack, Stroke, Asthma Attack, Panic Attack, or Unknown. "
            f"Determine the severity level (Critical, High, Moderate, Low) and provide the correct first-aid protocol."
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult,
                temperature=0.1
            )
        )
        
        data = json.loads(response.text)
        return TriageResult(**data)
