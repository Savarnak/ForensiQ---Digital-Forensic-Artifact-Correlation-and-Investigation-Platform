# ARGUS Backend Foundation

FastAPI & SQLAlchemy Async backend engine for ARGUS — Agentic Investigation Backbone.

## 📁 Backend Directory Structure

```
backend/
├── app/
│   ├── api/             # FastAPI REST endpoints (/cases, /evidence, /goals, /investigations, etc.)
│   ├── core/            # Config, Async SQLAlchemy DB session, logging, Neo4j, Qdrant
│   ├── models/          # SQLAlchemy 2.0 async domain models (Case, Evidence, InvestigationGoal, etc.)
│   ├── schemas/         # Pydantic v2 schemas for request/response validation
│   ├── services/        # Business logic & database operations layer
│   ├── agents/          # Agent definitions and extraction abstractions
│   ├── evidence/        # Evidence ingestion & processing handlers
│   ├── correlation/     # Entity resolution & correlation engine
│   ├── memory/          # Episodic & persistent memory management
│   └── knowledge_graph/ # Knowledge graph builders & query interfaces
├── tests/               # Pytest suite for API endpoints and services
├── main.py              # Root ASGI server entrypoint
├── requirements.txt     # Python dependencies
└── argus_local.db       # Local SQLite database (created automatically if PostgreSQL is omitted)
```

## 🚀 Setup & Execution Instructions

### 1. Prerequisites
- Python 3.11+
- Virtual Environment (recommended)

### 2. Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Run FastAPI Application
```bash
# Run locally using Uvicorn
python main.py
```
- Server will run at: `http://localhost:8000`
- Swagger Interactive Documentation: `http://localhost:8000/api/docs`
- ReDoc Documentation: `http://localhost:8000/api/redoc`

### 4. Database Options

#### Option A: Lightweight SQLite (Default for rapid local dev)
No additional setup needed. SQLite DB file `argus_local.db` will automatically be initialized.

#### Option B: PostgreSQL (Production & Containerized mode)
Set `USE_POSTGRES=true` in `.env` or set `DATABASE_URL=postgresql+asyncpg://argus_user:argus_password@localhost:5432/argus_db` and spin up PostgreSQL using Docker:
```bash
# From project root
docker-compose up -d postgres
```

### 5. Running Automated Test Suite
```bash
python -m pytest tests -v
```
