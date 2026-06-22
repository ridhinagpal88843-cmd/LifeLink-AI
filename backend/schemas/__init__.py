"""
Schemas Layer (Pydantic Validation & Serialization DTOs)
=======================================================

This module contains Pydantic models used to define:
1. API request payloads (e.g. TelemetryPayload, DispatchRequest).
2. API response payloads (e.g. TriageResponse, RouteResponse, AlertOut).
3. Data verification constraints and custom field validations.

These schemas act as Data Transfer Objects (DTOs), ensuring strict validation 
and documentation support for the FastAPI endpoints.
"""
