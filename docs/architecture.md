# ARGUS System Architecture

**Project Name**: ARGUS — Agentic Investigation Backbone  
**Document Version**: 1.0.0  
**Core Design Principle**: `ARGUS = Orchestration Backbone + Modular Tools/Agents`

---

## 1. High-Level System Architecture

ARGUS is an agentic investigation support platform designed for law enforcement investigators. It decouples high-level reasoning and planning (the **Brain**) from execution capabilities (the **Hands**) and multi-modal case persistence (the **Notepad**).

```mermaid
graph TD
    subgraph Frontend["ARGUS Frontend (React + Vite + Tailwind CSS)"]
        UI_Workspace["Case Workspace & Goal Input"]
        UI_Vault["Digital Evidence Vault"]
        UI_Graph["Interactive Knowledge Graph (Cytoscape/Vis)"]
        UI_Timeline["Reconstructed Timeline Swimlanes"]
        UI_Leads["Human-in-the-Loop Lead Review Board"]
    end

    subgraph REST_API["FastAPI API Gateway Layer"]
        API_Cases["/api/v1/cases"]
        API_Evidence["/api/v1/evidence"]
        API_Orchestrator["/api/v1/orchestrator"]
        API_Leads["/api/v1/leads"]
        API_Health["/api/v1/health"]
    end

    subgraph Brain["LangGraph Brain Orchestrator"]
        Planner["Task Decomposition Planner"]
        Selector["Dynamic Tool Selector"]
        Executor_Node["Execution Dispatcher"]
        Evaluator["Task Evaluator & Re-planner"]
        Lead_Gen["Hypothesis & Lead Generator"]
    end

    subgraph Hands["Modular Tool Registry ('Hands')"]
        Tool_Exif["Exif & Metadata Extractor"]
        Tool_OCR["OCR Text Extractor"]
        Tool_Entity["Entity & Handle Extractor"]
        Tool_Vector["Vector Indexer"]
        Tool_Custom["Extensible Custom Tools..."]
    end

    subgraph Notepad["Notepad Memory Store"]
        Postgres[(PostgreSQL - Cases, Evidence, Findings, Audit)]
        Neo4j[(Neo4j - Entity Relation Graph)]
        Qdrant[(Qdrant - Vector Search Embeddings)]
    end

    UI_Workspace --> API_Cases
    UI_Vault --> API_Evidence
    UI_Leads --> API_Leads
    UI_Graph --> API_Orchestrator
    UI_Timeline --> API_Orchestrator

    API_Orchestrator --> Brain

    Planner --> Selector
    Selector --> Executor_Node
    Executor_Node --> Hands
    Hands --> Evaluator
    Evaluator -->|New Tasks Required| Planner
    Evaluator -->|Complete| Lead_Gen

    Hands -->|Structured Findings + Provenance| Postgres
    Hands -->|Nodes & Edges| Neo4j
    Hands -->|Vector Chunks| Qdrant

    Lead_Gen -->|Proposed Leads| Postgres
```

---

## 2. Backend Module Structure

The backend is built with Python 3.11+, FastAPI, SQLAlchemy, and LangGraph, organized in a modular structure to enforce clear separation of concerns.

```mermaid
graph TD
    subgraph Backend_Structure["ARGUS Backend Module Layout"]
        Main["main.py (FastAPI App & Lifespan)"]
        
        subgraph App_Package["app/"]
            subgraph Core["app/core/"]
                Config["config.py (Pydantic Settings)"]
                DB["database.py (SQLAlchemy Async Engine)"]
                Neo4j_Client["neo4j.py (Graph DB Client)"]
                Qdrant_Client["qdrant.py (Vector DB Client)"]
                Logging["logging.py (Structured Logs)"]
            end

            subgraph Models["app/models/"]
                Case_Model["case.py (Case & Status Enum)"]
                Evidence_Model["evidence.py (Evidence File Models)"]
                Finding_Model["finding.py (Structured Findings + Provenance)"]
                Lead_Model["lead.py (Leads & HITL Review Status)"]
                Audit_Model["audit.py (AI Action Audit Log)"]
            end

            subgraph Tools["app/tools/"]
                Tool_Registry["registry.py (ToolRegistry & BaseTool Decorator)"]
                Metadata_Tool["metadata_tool.py (ExifRead & Pillow)"]
                OCR_Tool["ocr_tool.py (Tesseract / EasyOCR)"]
                Entity_Tool["entity_tool.py (Handle, Phone, Email Regex/NLP)"]
                Vector_Tool["vector_tool.py (Embeddings & Qdrant Upsert)"]
            end

            subgraph Orchestrator["app/orchestrator/"]
                State["state.py (LangGraph CaseState Schema)"]
                Planner_Node["planner.py (Decomposer Node)"]
                Executor_Node["executor.py (Tool Runner Node)"]
                Correlator_Node["correlator.py (Entity Res & Graph Syncer)"]
                Lead_Generator_Node["lead_generator.py (Explainable Lead Proposer)"]
                Brain_Graph["brain_graph.py (StateGraph Assembly)"]
            end

            subgraph API["app/api/"]
                Router["router.py (Main Router Aggregator)"]
                Cases_API["cases.py"]
                Evidence_API["evidence.py"]
                Leads_API["leads.py"]
                Orchestrator_API["orchestrator.py"]
                Health_API["health.py"]
            end
        end
    end

    Main --> Router
    Router --> Cases_API
    Router --> Evidence_API
    Router --> Leads_API
    Router --> Orchestrator_API
    Orchestrator_API --> Brain_Graph
    Brain_Graph --> State
    Brain_Graph --> Planner_Node
    Brain_Graph --> Executor_Node
    Executor_Node --> Tool_Registry
```

---

## 3. Frontend Module Structure

The frontend is a single-page application (SPA) powered by React 18, Vite, and Tailwind CSS.

```mermaid
graph TD
    subgraph Frontend_Structure["ARGUS Frontend Component Hierarchy"]
        App["App.jsx (Main Layout & State Container)"]
        Header["Header.jsx (Status Badges & Active Case Indicator)"]
        
        subgraph Views["Dashboard View Panels"]
            CaseWorkspace["CaseWorkspace.jsx (Case Selector & Goal Form)"]
            EvidenceVault["EvidenceIngestion.jsx (Multi-Modal Vault & Demo Loader)"]
            
            subgraph Tabs["Investigation Analysis Tabs"]
                KnowledgeGraph["KnowledgeGraph.jsx (Interactive Entity Topology)"]
                TimelineViewer["TimelineViewer.jsx (Chronological Swimlanes)"]
                LeadReviewBoard["LeadReviewBoard.jsx (Human-in-the-Loop Review Gate)"]
              end
        end

        subgraph Modals["Overlay Components"]
            ExecutionLogsModal["ExecutionLogsModal.jsx (Real-Time Brain Logs)"]
        end

        subgraph Services["Services & Client"]
            API_Client["services/api.js (REST API Client)"]
        end
    end

    App --> Header
    App --> CaseWorkspace
    App --> EvidenceVault
    App --> KnowledgeGraph
    App --> TimelineViewer
    App --> LeadReviewBoard
    App --> ExecutionLogsModal
    
    CaseWorkspace --> API_Client
    EvidenceVault --> API_Client
    LeadReviewBoard --> API_Client
```

---

## 4. End-to-End Investigation Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Investigator as Law Enforcement Investigator
    participant UI as ARGUS React Frontend
    participant API as FastAPI Backend
    participant Brain as LangGraph Brain Orchestrator
    participant Registry as Tool Registry ("Hands")
    participant Notepad as Notepad Memory (Postgres/Neo4j/Qdrant)

    Investigator->>UI: 1. Input Case Goal & Upload Evidence Files
    UI->>API: POST /api/v1/cases & POST /api/v1/evidence/upload
    API->>Notepad: Store Case metadata & raw Evidence files
    
    Investigator->>UI: 2. Click "Run ARGUS Orchestrator"
    UI->>API: POST /api/v1/orchestrator/run/{case_id}
    API->>Brain: Invoke StateGraph(CaseState)

    Brain->>Registry: Query list_tools()
    Registry-->>Brain: Return available tool capabilities & schemas
    Brain->>Brain: Planner Node decomposes goal into sub-tasks

    loop For each planned task
        Brain->>Registry: Dispatch tool by name (e.g. exif_extractor)
        Registry->>Notepad: Execute tool & store raw findings + provenance
    end

    Brain->>Brain: Correlator Node performs entity resolution
    Brain->>Notepad: Sync graph nodes/edges to Neo4j & vectors to Qdrant

    Brain->>Brain: Lead Generator Node synthesizes hypotheses
    Brain->>Notepad: Save proposed leads with PROPOSED status

    API-->>UI: Return final state, graph topology, & proposed leads
    UI-->>Investigator: Display Knowledge Graph, Timeline, & Lead Review Board

    Investigator->>UI: 3. Review Lead evidence provenance & click "Approve"
    UI->>API: PATCH /api/v1/leads/{lead_id}/review (Action: APPROVED)
    API->>Notepad: Update Lead status to INVESTIGATOR_APPROVED & write AuditLog
    API-->>UI: Confirm Lead approval & update UI state
```

---

## 5. Security & Human-in-the-Loop Architecture

ARGUS operates under strict security and legal accountability boundaries:

1. **Non-Autonomous Consequential Actions**: ARGUS never makes final determinations of guilt, enforcement action, or target identification. The system generates **Investigative Recommendations** with `PROPOSED` status.
2. **Investigator Approval Gate**: Consequential leads require explicit review by an authorized investigator providing their Badge/Investigator ID and optional justification notes.
3. **Immutable Provenance Trace**: Every finding or proposed lead must retain:
   - `source_evidence_id`
   - `source_tool_name`
   - `confidence_score` (0.0 - 1.0)
   - `reasoning_chain`
   - `timestamp`
   - `case_id`
4. **Audit Trail Logging**: Every AI planning step, tool execution, and investigator decision is written to the `audit_logs` table for court admissibility and internal compliance.
