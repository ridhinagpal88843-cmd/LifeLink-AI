import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.emergency_incident import EmergencyIncident, IncidentStateTransition
from backend.mcp.client import MCPClientRegistry

logger = logging.getLogger(__name__)


class AuditAgent:
    """
    Agent responsible for logging system transitions and action audits,
    integrating with Logging MCP Tool.
    """

    def __init__(self, db: Session, mcp_client: Optional[MCPClientRegistry] = None):
        self.db = db
        self.mcp_client = mcp_client

    def record_transition(self, incident: EmergencyIncident, status: str, notes: Optional[str] = None):
        """
        Atomically records a transition step in the database.
        """
        transition = IncidentStateTransition(
            incident_id=incident.id,
            status=status,
            notes=notes,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(transition)
        incident.status = status
        self.db.commit()
        logger.info(f"AUDIT AGENT: Logging Transition -> [{status}]: {notes}")

    def log_actions(self, incident_id: str, actions: List[str]):
        """
        Commits general system action executions to the Logging MCP tool.
        """
        for action in actions:
            if self.mcp_client:
                self.mcp_client.logging_log_action(incident_id, action)
            else:
                logger.info(f"FALLBACK AUDIT [Incident {incident_id}]: {action}")

