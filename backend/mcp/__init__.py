"""
Model Context Protocol (MCP) Integration Layer
==============================================

This package exports the MCP Client Integration interfaces:
- MCPClientRegistry: Central tool execution registry for Patient DB, Maps, 
  Doctor Directory, Voice Calls, and Audit Logging.
"""

from backend.mcp.client import MCPClientRegistry

__all__ = ["MCPClientRegistry"]
