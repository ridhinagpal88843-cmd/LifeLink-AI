"""
API Controllers Layer (FastAPI Routers)
=======================================

This module contains the HTTP interfaces and request handlers for the application.

It organizes REST routes:
- /api/v1/telemetry: Ingests incoming sensor telemetry data stream.
- /api/v1/alerts: Fetches or updates existing active alert instances.
- /api/v1/dispatch: Orchestrator-driven resource allocation routes.

It handles HTTP validations, maps incoming structures to schemas, calls the 
underlying services, and returns formatted JSON outputs.
"""
