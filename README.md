# ARGUS — Agentic Investigation Backbone

Proof-of-concept investigation support platform for authorized law-enforcement investigators, powered by an agentic orchestration backbone (*Brain, Hands, Notepad*).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), PostgreSQL / SQLite
- **Orchestration & Agents**: LangGraph, Dynamic Tool Registry Framework
- **Databases (Notepad Memory)**:
  - **PostgreSQL**: Relational case, evidence, findings, goals, investigation runs, and audit events.
  - **Neo4j**: Entity resolution & relationship knowledge graph.
  - **Qdrant**: Vector database for semantic evidence retrieval.
- **Frontend**: React 18, Vite, Tailwind CSS

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- Docker Desktop (Optional, for running PostgreSQL, Neo4j, Qdrant in containers)

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Backend Setup & Local Run
From the project root:
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server locally
python main.py
```
The API server will start at `http://localhost:8000`.  
Swagger API Documentation is accessible at `http://localhost:8000/api/docs`.

### 4. Running Infrastructure with Docker (Optional)
To run PostgreSQL, Neo4j, and Qdrant in Docker containers:
```bash
docker-compose up -d
```

### 5. Running Automated Backend Tests
```bash
python -m pytest backend/tests -v
```

### 6. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
The React frontend dashboard will open at `http://localhost:3000`.

---

## 🛰️ REST API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/cases` | Create a new investigation case |
| `GET` | `/api/cases` | List all investigation cases |
| `GET` | `/api/cases/{case_id}` | Get detailed case info |
| `POST` | `/api/cases/{case_id}/evidence` | Upload digital evidence file |
| `GET` | `/api/cases/{case_id}/evidence` | List all evidence for a case |
| `POST` | `/api/cases/{case_id}/goals` | Add an investigation goal |
| `GET` | `/api/cases/{case_id}/goals` | List goals for a case |
| `POST` | `/api/cases/{case_id}/investigations` | Initialize an investigation run |
| `GET` | `/api/cases/{case_id}/investigations` | List investigation runs for a case |
| `POST` | `/api/orchestrator/run/{case_id}` | Trigger LangGraph brain orchestration |
| `PATCH` | `/api/leads/{lead_id}/review` | Human-in-the-Loop review lead decision |
