"""
Model Context Protocol (MCP) Integration Layer
==============================================

This module manages client/server implementations for the Model Context Protocol.

It exposes critical tools and resources to Gemini AI models and Google ADK agents:
- Hospital Resource Tools: Fetching real-time ICU bed availability or specialist status.
- Traffic & Dispatch Tools: Simulating traffic conditions and ambulance routing paths.
- Electronic Health Records (EHR) Tools: Pulling mock patient charts or allergy histories.

By wrapping external systems (SQL databases, third-party APIs) as MCP tools, 
we provide standard, unified data access interfaces to our AI agents.
"""
