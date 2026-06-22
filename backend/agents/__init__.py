"""
Agents Layer (Google ADK Definitions)
=====================================

This module contains specialized agent definitions powered by the Google 
Agent Development Kit (ADK) and Gemini API. 

Each agent represents a distinct domain expert role in the emergency 
healthcare coordination workflow:
- TriageAgent: Analyzes input patient telemetry data to assess severity level.
- ResourceAllocationAgent: Identifies hospitals with available ICU beds or equipment.
- DispatcherAgent: Coordinates ambulance routing and ETA updates.

All agents are framework-agnostic and focus strictly on their cognitive task 
using specialized instructions, prompts, and tool interfaces.
"""
