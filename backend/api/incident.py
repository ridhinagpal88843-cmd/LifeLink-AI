from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.emergency_incident import EmergencyIncident
from backend.schemas.emergency_incident import EmergencyIncidentResponse, EmergencyIncidentUpdate, EmergencyIncidentCreate
from backend.orchestrator.workflow_manager import EmergencyWorkflowManager

router = APIRouter(prefix="/emergency", tags=["Emergency Incidents"])


@router.post("/trigger", response_model=EmergencyIncidentResponse, status_code=201)
async def trigger_emergency(
    payload: EmergencyIncidentCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Triggers the multi-agent emergency coordination workflow for a patient.
    Ingests vital telemetry and executes triage and parallel notifications.
    """
    try:
        manager = EmergencyWorkflowManager(db)
        telemetry_data = {
            "emergency_type": payload.emergency_type,
            "severity": payload.severity,
            "latitude": payload.latitude,
            "longitude": payload.longitude
        }
        # In a real setup, we would append SpO2/Heart rate telemetry from payload if available
        incident = await manager.trigger_emergency_workflow(user_id=user_id, telemetry_data=telemetry_data)
        return incident
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{incident_id}/location", response_model=EmergencyIncidentResponse)
async def update_location(
    incident_id: str,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    """
    Pushes live coordinate telemetry updates from an active ambulance,
    re-calculating travel duration and generating audit logs.
    """
    try:
        manager = EmergencyWorkflowManager(db)
        incident = await manager.update_incident_location(
            incident_id=incident_id,
            latitude=latitude,
            longitude=longitude
        )
        return incident
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history", response_model=List[EmergencyIncidentResponse])
def get_incident_history(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves all past and active incidents logged for a specific patient.
    """
    incidents = db.query(EmergencyIncident).filter(EmergencyIncident.user_id == user_id).order_by(EmergencyIncident.created_at.desc()).all()
    return incidents


@router.get("/{incident_id}", response_model=EmergencyIncidentResponse)
def get_incident_details(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches the status and chronological transition logs of a single incident.
    """
    incident = db.query(EmergencyIncident).filter(EmergencyIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return incident
