"""
Services Layer (Core Business Logic & Use Cases)
================================================

This module encapsulates all application business logic. 

Examples of services implemented here include:
- EmergencyCoordinationService: Orchestrates the sequence of events from receiving 
  telemetry data to dispatching resources.
- TelemetryAnalysisService: Calculates thresholds and triggers emergency flags 
  from raw sensor details.
- RouteOptimizationService: Calculates shortest path calculations using coordinate systems.

Services remain framework-agnostic, receiving database connections or agent 
instances via dependency injection to preserve clean separation.
"""
