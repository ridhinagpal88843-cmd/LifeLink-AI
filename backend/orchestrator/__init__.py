"""
Orchestrator Layer (Multi-Agent Coordination & Workflow Engine)
================================================================

This module acts as the control center of the LifeLink AI system. It is 
responsible for:
1. Ingesting emergency vitals and telemetry streams.
2. Managing the sequence flow across Triage, Resource, and Dispatch ADK agents.
3. Locking immutable patient clinical snapshots for audit logs.
4. Sending priority notifications to primary doctors and emergency contacts.
"""

from backend.orchestrator.workflow_manager import EmergencyWorkflowManager

__all__ = ["EmergencyWorkflowManager"]
