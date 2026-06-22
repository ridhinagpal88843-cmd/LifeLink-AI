"""
Orchestrator Layer (Multi-Agent Coordination & Workflow Engine)
================================================================

This module acts as the control center of the LifeLink AI system. It is 
responsible for:
1. Receiving and parsing incoming emergency telemetry streams.
2. Directing workflow execution across multiple AI agents (Triage, Resource, Dispatch).
3. Maintaining execution state (chat histories, current dispatch phases, ETAs).
4. Invoking the appropriate Model Context Protocol (MCP) server tools to retrieve 
   or modify external resources.

This layer implements coordination logic without hardcoding specific agent 
behavior, keeping agents independent and modular.
"""
