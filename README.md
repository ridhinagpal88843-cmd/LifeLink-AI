# LifeLink AI 🚑🤖

**LifeLink AI** is a production-ready, AI-powered emergency healthcare coordination system. Using the **Google Agent Development Kit (ADK)** and the **Model Context Protocol (MCP)**, the system accepts telemetry streams from emergency sensors (wearables, smart devices, etc.), processes clinical data, and coordinates specialized AI agents (Triage, Dispatch, Resource Allocation) to minimize response times.

---

## 🏛️ Clean Architecture Design

The project strictly follows **Clean Architecture** principles to separate concerns, keep layers decoupled, and allow for independent testability:

```text
               ┌──────────────────────────────┐
               │           API / UI           │ (External Interface: FastAPI / Streamlit)
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    Services / Orchestrator   │ (Use Cases / Core Business Logic)
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │       Agents / Models        │ (Domain Entities & AI Agent Defs)
               └──────────────────────────────┘
```

- **Independent Layers**: Outer layers depend on inner layers, but inner layers remain entirely agnostic of frameworks (FastAPI, SQLite, SQLAlchemy, etc.).
- **Domain Independence**: Models and business services do not contain reference to database queries or API router definitions.
- **Agent Orchestration**: Handled by the Orchestrator layer, driving ADK-powered agents that invoke tools via MCP servers.

---

## 📂 Project Directory Structure

```text
LIFELINK/
├── requirements.txt         # Project dependencies
├── .env.example             # Configuration environment template
├── .gitignore               # Ignored files for git control
├── README.md                # System document overview (this file)
├── backend/                 # Backend FastAPI and AI Orchestration Core
│   ├── __init__.py          # Module initialization
│   ├── main.py              # Application entry point
│   ├── config.py            # Environment-aware settings manager (Pydantic Settings)
│   ├── database.py          # SQLAlchemy engine and session initializer
│   ├── agents/              # Google ADK agent configurations and profiles
│   ├── orchestrator/        # Multi-agent coordination logic and telemetry router
│   ├── mcp/                 # Model Context Protocol servers/tools
│   ├── database/            # DB scripts, seeding, and migrations configurations
│   ├── models/              # SQLAlchemy domain models (Entities)
│   ├── schemas/             # Pydantic schemas (Data Transfer Objects & validation)
│   ├── services/            # Pure domain services (Use-case implementations)
│   ├── security/            # API Key, RBAC, and credentials security logic
│   ├── api/                 # FastAPI routes / endpoints (Controllers)
│   ├── utils/               # Common helper packages (logging, mapping)
│   └── config/              # YAML/JSON config loader overrides
├── frontend/                # Frontend dashboard structure
│   └── app.py               # Streamlit application dashboard
├── docs/                    # Technical & Architectural documentation
│   └── architecture.md      # Explanatory system flow diagrams
└── tests/                   # Test suite scaffolding
    ├── conftest.py          # Pytest shared fixtures
    ├── unit/                # Layer unit tests
    └── integration/         # Endpoint and agent integration tests
```

---

## 🚀 Getting Started

### 📋 Prerequisites
- Python 3.12 or newer
- SQLite (included with Python)

### ⚙️ Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd LIFELINK
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Open .env and add your GEMINI_API_KEY
   ```

5. **Run the Backend API**
   ```bash
   uvicorn backend.main:app --reload
   ```
   The backend API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000). You can explore Swagger API docs at `/docs`.

6. **Run the Frontend Dashboard**
   ```bash
   streamlit run frontend/app.py
   ```
   The Streamlit simulation app will open in your web browser.

---

## 🧪 Running Tests
To run the automated tests, execute:
```bash
pytest
```
