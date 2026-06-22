"""
Security Layer (Authentication, Authorization & API Verification)
================================================================

This module secures the FastAPI endpoints and data channels:
- API Key check: Validating telemetry streams arriving from certified emergency 
  devices or simulators.
- JWT Session checks: Supporting credentials verification for the Streamlit dashboard 
  or external portals.
- Role-Based Access Control (RBAC): Guaranteeing only authorized medical staff or 
  dispatchers can access sensitive clinical resources or invoke routing overrides.
"""
