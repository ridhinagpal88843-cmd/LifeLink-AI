# LifeLink AI - Architectural Blueprint 🏛️

This document describes the architectural layout, communication boundaries, and clean design patterns implemented in **LifeLink AI**.

## Clean Architecture Principles

LifeLink AI is structured according to Clean Architecture concepts, separating the application into four distinct rings of responsibility:

```text
       ┌─────────────────────────────────────────────────────────┐
       │                        Frameworks                       │
       │           (FastAPI, Uvicorn, Streamlit, SQLite)         │
       │                                                         │
       │       ┌─────────────────────────────────────────┐       │
       │       │                Adapters                 │       │
       │       │    (SQLAlchemy Repos, FastAPI Routers)  │       │
       │       │                                         │       │
       │       │       ┌─────────────────────────┐       │       │
       │       │       │       Application       │       │       │
       │       │       │  (Use Cases & Services) │       │       │
       │       │       │                         │       │       │
       │       │       │       ┌─────────┐       │       │       │
       │       │       │       │ Domain  │       │       │       │
       │       │       │       │ (Models)│       │       │       │
       │       │       │       └─────────┘       │       │       │
       │       │       └─────────────────────────┘       │       │
       │       └─────────────────────────────────────────┘       │
       └─────────────────────────────────────────────────────────┘
```

1. **Domain Layer (`backend/models/`)**: Specifies core business entities (`Alert`, `Patient`, `Hospital`, `Ambulance`) completely decoupled from database engine drivers or web interfaces.
2. **Application Layer (`backend/services/`, `backend/agents/`)**: Core application logic. Contains the AI Agents defined using the Google Agent Development Kit (ADK).
3. **Interface Adapters (`backend/api/`, `backend/mcp/`)**: Bridges controllers and endpoints. Receives web traffic, parses schemas via Pydantic, and handles Model Context Protocol (MCP) data tool mappings.
4. **Infrastructure Layer (`backend/database/`, `backend/config/`)**: Database engines, configurations, migrations, external server bindings.

---

## AI Multi-Agent & MCP Data Flow

Below is the telemetry triage & dispatch flow diagram:

```mermaid
sequenceDiagram
    autonumber
    participant Telemetry as Telemetry Simulator
    participant API as FastAPI Router (/telemetry)
    participant Orch as Orchestrator Service
    participant Triage as Triage Agent (ADK)
    participant MCP as MCP Tools Server
    participant Dispatch as Dispatch Agent (ADK)

    Telemetry->>API: Post telemetry vitals (Heart rate, GPS)
    API->>Orch: Dispatch alert workflow
    Orch->>Triage: Assess vitals severity
    Triage-->>Orch: returns severity level (e.g. Critical)
    Orch->>MCP: Query closest available ICU beds
    MCP-->>Orch: returns closest hospitals list
    Orch->>Dispatch: Determine best routing and ETA
    Dispatch-->>Orch: returns selected vehicle & route
    Orch->>API: Return response state
    API-->>Telemetry: HTTP 200 (Success Dispatch)
```

## Module Independence Rules
- **No Circular Imports**: Submodules do not import from parents. Communication goes downwards.
- **Pydantic Validation**: All data traversing the network boundaries is verified by `backend/schemas/`.
- **Database Dependency Injection**: Database sessions (`SessionLocal`) are never globally imported inside services or API routes; they are yielded through FastAPI's `Depends(get_db)` to ensure isolated transaction scopes.
