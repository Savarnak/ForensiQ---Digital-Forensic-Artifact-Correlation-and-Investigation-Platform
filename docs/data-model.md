# ARGUS Data Model & Knowledge Graph Schema

**Document Version**: 1.0.0  
**Storage Layers**: PostgreSQL (Relational), Neo4j (Graph), Qdrant (Vector)

---

## 1. Relational Database Schema (PostgreSQL / SQLite)

The relational database manages case metadata, raw evidence references, structured findings with provenance, human-in-the-loop lead decisions, and AI action audit logs.

```mermaid
erDiagram
    CASES ||--o{ EVIDENCE : "contains"
    CASES ||--o{ FINDINGS : "stores"
    CASES ||--o{ LEADS : "proposes"
    CASES ||--o{ AUDIT_LOGS : "logs"
    EVIDENCE ||--o{ FINDINGS : "produces"

    CASES {
        string id PK "UUID4"
        string case_number UK "Indexed"
        string title
        text description
        text investigation_goal
        string status "ACTIVE | PAUSED | CLOSED"
        datetime created_at
        datetime updated_at
    }

    EVIDENCE {
        string id PK "UUID4"
        string case_id FK
        string file_name
        string file_path
        string file_type "IMAGE | CHAT_LOG | AUDIO | DOCUMENT"
        string mime_type
        string hash_sha256
        string file_size_bytes
        datetime uploaded_at
        json extracted_metadata
    }

    FINDINGS {
        string id PK "UUID4"
        string case_id FK
        string evidence_id FK
        string tool_name
        string finding_type "ENTITY | GPS | OCR_TEXT | TIMELINE_EVENT"
        json content "Structured extracted data"
        float confidence "0.0 - 1.0"
        datetime extracted_at
        json provenance "Source evidence, tool, execution time"
    }

    LEADS {
        string id PK "UUID4"
        string case_id FK
        string title
        text summary
        string status "PROPOSED | INVESTIGATOR_APPROVED | INVESTIGATOR_REJECTED"
        float confidence
        json supporting_evidence_ids
        json reasoning_chain
        json next_recommended_actions
        datetime created_at
        datetime reviewed_at
        string reviewed_by "Investigator ID"
        text reviewer_notes
    }

    AUDIT_LOGS {
        string id PK "UUID4"
        string case_id FK
        string action_type "PLAN_DECOMPOSED | TOOL_EXECUTED | LEAD_REVIEWED"
        string agent_name
        text input_summary
        text output_summary
        json details
        datetime timestamp
    }
```

---

## 2. Knowledge Graph Schema (Neo4j)

The Neo4j graph represents resolved entities and cross-evidence relationship topologies.

```mermaid
graph TD
    subgraph Graph_Nodes["Neo4j Entity Node Types"]
        Node_Person["(:Person {handle, name})"]
        Node_Device["(:Device {device_id, make, model})"]
        Node_Loc["(:Location {name, latitude, longitude})"]
        Node_Acc["(:Account {platform, email})"]
        Node_Ev["(:Evidence {id, file_name, file_type})"]
    end

    Node_Person -->|COMMUNICATED_WITH| Node_Person
    Node_Person -->|USED_BY| Node_Device
    Node_Person -->|OWNED_BY| Node_Acc
    Node_Person -->|MENTIONED_IN| Node_Ev
    Node_Device -->|GEOTAGGED_AT| Node_Loc
    Node_Ev -->|CAPTURED_AT| Node_Loc
```

### Neo4j Cypher Constraints
```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.handle IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
```

---

## 3. Vector Database Collection Schema (Qdrant)

The Qdrant collection stores 384-dimensional dense vectors generated from evidence text chunks, OCR output, and document snippets.

### Collection Specs
- **Collection Name**: `argus_evidence_vectors`
- **Vector Dimensions**: `384`
- **Distance Metric**: `Cosine`

### Vector Payload Schema (JSON)
```json
{
  "id": "c7b60e6e-6701-4475-8025-a837e28b17ff",
  "vector": [0.042, -0.118, 0.891, "...(384 floats)"],
  "payload": {
    "case_id": "c92881a5-8121-4f9e-b9b2-9111ab12ef01",
    "evidence_id": "ev-001-chat-log",
    "file_path": "./data/evidence/synthetic_chat_log.txt",
    "text_snippet": "@CyberHawk: Are you ready for the sync? @NightOwl: Yes at meeting location...",
    "source_tool": "ocr_text_extractor"
  }
}
```

---

## 4. Evidence & Finding Data Models (Pydantic / Python)

```python
class ProvenanceModel(BaseModel):
    source_evidence: str
    source_tool: str
    task_id: str
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FindingModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    evidence_id: Optional[str] = None
    tool_name: str
    finding_type: str
    content: Dict[str, Any]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: ProvenanceModel
```
