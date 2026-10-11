from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Dict, Any
from datetime import datetime
import uuid
import json

from app.core.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.lead import Lead, LeadStatus
from app.models.run import InvestigationRun
from app.models.task import InvestigationTask
from app.models.audit import AuditEvent
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.orchestrator.state import CaseState
from app.orchestrator.brain_graph import investigation_graph
from app.core.logging import logger

router = APIRouter(prefix="/orchestrator", tags=["Investigation Brain Orchestrator"])

@router.post("/run/{case_id}")
async def run_investigation(case_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Fetch Case
    case_res = await db.execute(select(Case).filter(Case.id == case_id))
    case_obj = case_res.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found.")

    # 2. Fetch Evidence
    ev_res = await db.execute(select(Evidence).filter(Evidence.case_id == case_id))
    evidence_items = ev_res.scalars().all()
    
    ev_list = [
        {
            "id": e.id,
            "file_name": e.file_name,
            "file_path": e.file_path,
            "file_type": e.file_type,
            "mime_type": e.mime_type,
            "extracted_metadata": e.extracted_metadata
        }
        for e in evidence_items
    ]

    # 3. Create Investigation Run record
    now_dt = datetime.utcnow()
    investigation_run_db = InvestigationRun(
        case_id=case_id,
        status="RUNNING",
        summary=f"Running agentic investigation planner for Case {case_obj.case_number}",
        created_at=now_dt
    )
    db.add(investigation_run_db)
    await db.flush()
    run_id = investigation_run_db.id

    # 4. Construct Initial CaseState
    initial_state = CaseState(
        case_id=case_obj.id,
        case_number=case_obj.case_number,
        investigation_goal=case_obj.title or "Identify relationships between accounts, devices, locations and events",
        evidence_items=ev_list
    )

    # 5. Invoke LangGraph Orchestration Pipeline
    logger.info(f"Invoking ARGUS Brain Orchestrator for Case {case_obj.case_number} (Run ID: {run_id})...")
    state_input_dict = initial_state.model_dump() if hasattr(initial_state, "model_dump") else initial_state.dict()
    final_state_dict = await investigation_graph.ainvoke(state_input_dict)
    
    # 6. Persist Tasks into SQL DB (referencing run_id)
    # Clear previous tasks & findings for case_id to prevent accumulation across re-runs
    await db.execute(delete(InvestigationTask).filter(InvestigationTask.case_id == case_id))
    await db.execute(delete(Finding).filter(Finding.case_id == case_id))

    tasks_data = final_state_dict.get("tasks", [])
    for t in tasks_data:
        t_dict = t if isinstance(t, dict) else (t.model_dump() if hasattr(t, "model_dump") else t.dict())
        res_data = t_dict.get("result")
        if res_data:
            res_data = json.loads(json.dumps(res_data, default=str))

        task_db = InvestigationTask(
            investigation_run_id=run_id,
            case_id=case_id,
            tool_name=t_dict.get("tool_name", "unknown_tool"),
            objective=t_dict.get("objective", "Investigative step"),
            status=t_dict.get("status", "COMPLETED"),
            result=res_data
        )
        db.add(task_db)

    # 7. Persist Findings into SQL DB with Deterministic Deduplication
    raw_findings = final_state_dict.get("raw_findings", [])
    seen_db_keys = set()
    deduped_raw_findings = []
    
    for f in raw_findings:
        evidence_id = f.get("evidence_id") or ""
        tool_name = f.get("tool_name", "tool")
        finding_type = f.get("finding_type", "GENERAL")
        content = f.get("content", {})
        
        content_str = json.dumps(content, sort_keys=True) if isinstance(content, (dict, list)) else str(content)
        key = f"{case_id}_{evidence_id}_{tool_name}_{finding_type}_{content_str}"
        if key not in seen_db_keys:
            seen_db_keys.add(key)
            deduped_raw_findings.append(f)
            finding_db = Finding(
                case_id=case_id,
                evidence_id=f.get("evidence_id"),
                tool_name=tool_name,
                finding_type=finding_type,
                content=content,
                confidence=f.get("confidence", 0.95),
                provenance=f.get("provenance", {})
            )
            db.add(finding_db)

    # 8. Persist Generated Leads into SQL DB
    proposed_leads = final_state_dict.get("proposed_leads", [])
    created_leads = []
    
    # Delete previous leads for this case to avoid stale IDs on re-runs
    await db.execute(delete(Lead).filter(Lead.case_id == case_id))

    for l in proposed_leads:
        target_lead_id = l.get("lead_id") or l.get("id") or str(uuid.uuid4())
        lead_db = Lead(
            id=target_lead_id,
            case_id=case_id,
            title=l.get("title"),
            summary=l.get("summary"),
            priority=l.get("priority", "MEDIUM"),
            status=LeadStatus.PENDING_REVIEW,
            confidence=l.get("confidence", 0.85),
            supporting_evidence_ids=l.get("supporting_evidence_ids") or l.get("supporting_evidence") or [],
            supporting_findings=l.get("supporting_findings", []),
            reasoning_factors=l.get("reasoning_factors") or l.get("reasoning_chain") or [],
            reasoning_chain=l.get("reasoning_chain", []),
            next_recommended_actions=l.get("next_recommended_actions") or l.get("recommended_next_action") or [],
            disclaimer=l.get("disclaimer", "Investigative aid provided for officer/analyst review. Does not constitute a determination of guilt or administrative finding.")
        )
        db.add(lead_db)
        
        lead_dict = {
            "id": lead_db.id,
            "lead_id": lead_db.id,
            "case_id": case_id,
            "title": lead_db.title,
            "summary": lead_db.summary,
            "priority": lead_db.priority,
            "status": lead_db.status.value if hasattr(lead_db.status, "value") else str(lead_db.status),
            "confidence": lead_db.confidence,
            "supporting_evidence": lead_db.supporting_evidence_ids or [],
            "supporting_findings": lead_db.supporting_findings or [],
            "reasoning_factors": lead_db.reasoning_factors or [],
            "next_recommended_actions": lead_db.next_recommended_actions or [],
            "disclaimer": lead_db.disclaimer
        }
        created_leads.append(lead_dict)

    # 8.5 Persist Resolved Graph Entities & Relationships
    await db.execute(delete(Relationship).filter(Relationship.case_id == case_id))
    await db.execute(delete(Entity).filter(Entity.case_id == case_id))

    nodes_list = final_state_dict.get("knowledge_graph_nodes", [])
    edges_list = final_state_dict.get("knowledge_graph_edges", [])
    entity_db_map = {}

    for n in nodes_list:
        orig_node_id = n.get("id") or str(uuid.uuid4())
        ent_id = f"{case_id}_{orig_node_id}"
        entity_db = Entity(
            id=ent_id,
            case_id=case_id,
            entity_type=n.get("label", "ENTITY").upper(),
            name=n.get("name", "Unknown Entity"),
            identifier=orig_node_id,
            properties=n.get("properties", {})
        )
        db.add(entity_db)
        entity_db_map[orig_node_id] = entity_db

    for e in edges_list:
        src = e.get("source")
        tgt = e.get("target")
        if src in entity_db_map and tgt in entity_db_map:
            rel_db = Relationship(
                id=str(uuid.uuid4()),
                case_id=case_id,
                source_entity_id=entity_db_map[src].id,
                target_entity_id=entity_db_map[tgt].id,
                relationship_type=e.get("relationship", "ASSOCIATED_WITH"),
                confidence=e.get("confidence", 0.90),
                properties={
                    "supporting_evidence": e.get("supporting_evidence", []),
                    "disclaimer": e.get("disclaimer")
                }
            )
            db.add(rel_db)

    # 9. Update Investigation Run Status & Summary
    investigation_run_db.status = "COMPLETED"
    investigation_run_db.summary = final_state_dict.get("investigation_summary") or f"Completed investigation run for Case {case_obj.case_number}"
    investigation_run_db.completed_at = datetime.utcnow()

    # 10. Persist Audit Events
    audit_events_list = final_state_dict.get("audit_events", [])
    for ae in audit_events_list:
        audit_db = AuditEvent(
            case_id=case_id,
            event_type=ae.get("event_type", "ORCHESTRATION_EVENT"),
            actor=ae.get("actor", "ARGUS_LANGGRAPH_BRAIN"),
            details=ae.get("details", {})
        )
        db.add(audit_db)

    await db.commit()

    return {
        "status": "success",
        "investigation_run": {
            "id": run_id,
            "case_id": case_id,
            "status": "COMPLETED",
            "summary": investigation_run_db.summary,
            "created_at": str(investigation_run_db.created_at),
            "completed_at": str(investigation_run_db.completed_at)
        },
        "tasks": tasks_data,
        "findings": {
            "count": len(raw_findings),
            "raw": raw_findings,
            "standardized": final_state_dict.get("standardized_findings", [])
        },
        "correlations": {
            "knowledge_graph": {
                "nodes_count": len(final_state_dict.get("knowledge_graph_nodes", [])),
                "edges_count": len(final_state_dict.get("knowledge_graph_edges", [])),
                "nodes": final_state_dict.get("knowledge_graph_nodes", []),
                "edges": final_state_dict.get("knowledge_graph_edges", [])
            },
            "timeline_events": final_state_dict.get("timeline_events", [])
        },
        "leads": created_leads,
        "audit_events": audit_events_list,
        "execution_logs": final_state_dict.get("execution_logs", [])
    }

@router.get("/results/{case_id}")
async def get_orchestrator_results(case_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Fetch Case
    case_res = await db.execute(select(Case).filter(Case.id == case_id))
    case_obj = case_res.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found.")

    # 2. Fetch Latest Investigation Run for case
    run_res = await db.execute(
        select(InvestigationRun)
        .filter(InvestigationRun.case_id == case_id)
        .order_by(InvestigationRun.created_at.desc())
    )
    latest_run = run_res.scalars().first()
    if not latest_run:
        return None

    # 3. Fetch Tasks for latest_run
    tasks_res = await db.execute(
        select(InvestigationTask)
        .filter(InvestigationTask.investigation_run_id == latest_run.id)
    )
    tasks = tasks_res.scalars().all()
    tasks_data = [
        {
            "id": t.id,
            "tool_name": t.tool_name,
            "objective": t.objective,
            "status": t.status,
            "result": t.result
        }
        for t in tasks
    ]

    # 4. Fetch Findings for case (with deterministic deduplication)
    findings_res = await db.execute(
        select(Finding).filter(Finding.case_id == case_id).order_by(Finding.extracted_at.asc())
    )
    raw_findings = []
    seen_keys = set()
    for f in findings_res.scalars().all():
        content_str = json.dumps(f.content, sort_keys=True) if isinstance(f.content, (dict, list)) else str(f.content)
        key = f"{f.case_id}_{f.evidence_id}_{f.tool_name}_{f.finding_type}_{content_str}"
        if key not in seen_keys:
            seen_keys.add(key)
            raw_findings.append({
                "id": f.id,
                "evidence_id": f.evidence_id,
                "tool_name": f.tool_name,
                "finding_type": f.finding_type,
                "content": f.content,
                "confidence": f.confidence,
                "provenance": f.provenance
            })

    # 5. Fetch Leads for case
    leads_res = await db.execute(
        select(Lead).filter(Lead.case_id == case_id).order_by(Lead.created_at.desc())
    )
    leads_data = [
        {
            "id": l.id,
            "lead_id": l.id,
            "case_id": l.case_id,
            "title": l.title,
            "priority": l.priority or "MEDIUM",
            "summary": l.summary,
            "status": l.status.value if hasattr(l.status, "value") else str(l.status),
            "confidence": l.confidence,
            "supporting_evidence": l.supporting_evidence_ids or [],
            "supporting_findings": l.supporting_findings or [],
            "reasoning_factors": l.reasoning_factors or [],
            "next_recommended_actions": l.next_recommended_actions or [],
            "disclaimer": getattr(l, "disclaimer", "Investigative aid provided for officer/analyst review.")
        }
        for l in leads_res.scalars().all()
    ]

    # 6. Reconstruct Graph & Timeline correlations from findings/evidence
    ev_res = await db.execute(select(Evidence).filter(Evidence.case_id == case_id))
    ev_list = [{"id": e.id, "file_name": e.file_name, "file_type": e.file_type} for e in ev_res.scalars().all()]
    
    from app.correlation.fusion_service import IntelligenceFusionService
    from app.evidence.timeline_engine import TimelineEngine
    import os

    synthetic_dir = "./data/synthetic_cases/case_001" if os.path.exists("./data/synthetic_cases/case_001") else None
    
    # Check for persisted entities/relationships in DB
    ent_res = await db.execute(select(Entity).filter(Entity.case_id == case_id))
    db_entities = ent_res.scalars().all()
    rel_res = await db.execute(select(Relationship).filter(Relationship.case_id == case_id))
    db_relationships = rel_res.scalars().all()

    if db_entities:
        graph_nodes = [
            {
                "id": ent.identifier or ent.id,
                "label": ent.entity_type.title(),
                "name": ent.name,
                "properties": ent.properties
            }
            for ent in db_entities
        ]
        ent_id_to_ident = {ent.id: (ent.identifier or ent.id) for ent in db_entities}
        graph_edges = [
            {
                "source": ent_id_to_ident.get(r.source_entity_id, r.source_entity_id),
                "target": ent_id_to_ident.get(r.target_entity_id, r.target_entity_id),
                "relationship": r.relationship_type,
                "confidence": r.confidence,
                "supporting_evidence": r.properties.get("supporting_evidence", [])
            }
            for r in db_relationships
        ]
    else:
        nodes = IntelligenceFusionService.resolve_entities(raw_findings, ev_list)
        fusion_results = IntelligenceFusionService.detect_relationships_and_correlations(raw_findings, ev_list, nodes)
        graph_nodes = fusion_results.get("nodes", [])
        graph_edges = fusion_results.get("edges", [])

    # 5.5 Fetch Persisted Audit Events for case_id
    audit_res = await db.execute(
        select(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp.desc())
    )
    audit_events_data = [
        {
            "id": ae.id,
            "case_id": ae.case_id,
            "event_type": ae.event_type,
            "actor": ae.actor,
            "details": ae.details,
            "timestamp": ae.timestamp.isoformat() if hasattr(ae.timestamp, "isoformat") else str(ae.timestamp)
        }
        for ae in audit_res.scalars().all()
    ]

    timeline_results = TimelineEngine.build_timeline(ev_list, raw_findings, synthetic_dir)

    return {
        "status": "success",
        "investigation_run": {
            "id": latest_run.id,
            "case_id": case_id,
            "status": latest_run.status,
            "summary": latest_run.summary,
            "created_at": str(latest_run.created_at),
            "completed_at": str(latest_run.completed_at) if latest_run.completed_at else None
        },
        "tasks": tasks_data,
        "findings": {
            "count": len(raw_findings),
            "raw": raw_findings,
            "standardized": raw_findings
        },
        "correlations": {
            "knowledge_graph": {
                "nodes_count": len(graph_nodes),
                "edges_count": len(graph_edges),
                "nodes": graph_nodes,
                "edges": graph_edges
            },
            "timeline_events": timeline_results.get("timeline", [])
        },
        "leads": leads_data,
        "audit_events": audit_events_data,
        "execution_logs": []
    }
