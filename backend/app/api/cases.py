from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
import os
import uuid

from app.core.database import get_db
from app.schemas.case import CaseCreate, CaseResponse
from app.services.case_service import CaseService
from app.models.case import Case
from app.models.lead import Lead, LeadStatus, LEAD_DISCLAIMER_TEXT
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.audit import AuditEvent
from app.evidence.lead_engine import LeadEngine
from app.evidence.timeline_engine import TimelineEngine
from app.evidence.gap_contradiction_engine import GapContradictionEngine
from app.correlation.fusion_service import IntelligenceFusionService
from app.core.logging import logger

router = APIRouter(tags=["Cases & Leads Engine"])

@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, db: AsyncSession = Depends(get_db)):
    return await CaseService.create_case(db, payload)

@router.post("/cases/synthetic", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/cases/synthetic/case_001", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def load_synthetic_case(db: AsyncSession = Depends(get_db)):
    return await CaseService.load_synthetic_case(db)

@router.get("/cases", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    return await CaseService.list_cases(db)

@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    return await CaseService.get_case_by_id(db, case_id)

@router.get("/cases/{case_id}/audit")
async def get_case_audit_events(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    GET /api/cases/{case_id}/audit
    Queries and returns all persisted AuditEvent log records for the specified case,
    ordered by timestamp descending for immutable audit log auditing.
    """
    case_res = await db.execute(select(Case).filter(Case.id == case_id))
    case_obj = case_res.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Target case not found.")

    audit_res = await db.execute(
        select(AuditEvent)
        .filter(AuditEvent.case_id == case_id)
        .order_by(AuditEvent.timestamp.desc())
    )
    events = audit_res.scalars().all()
    return [
        {
            "id": e.id,
            "case_id": e.case_id,
            "event_type": e.event_type,
            "actor": e.actor,
            "details": e.details,
            "timestamp": e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp)
        }
        for e in events
    ]

@router.get("/cases/{case_id}/leads")
async def get_case_leads(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    GET /api/cases/{case_id}/leads
    Generates and returns candidate investigative leads with explainable priority scoring (HIGH/MEDIUM/LOW),
    transparent reasoning factors, supporting evidence citations, recommended next actions, and non-guilt disclaimers.
    """
    # 1. Fetch Case
    case_res = await db.execute(select(Case).filter(Case.id == case_id))
    case_obj = case_res.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Target case not found.")

    # 2. Fetch existing DB leads
    leads_res = await db.execute(select(Lead).filter(Lead.case_id == case_id).order_by(Lead.created_at.desc()))
    existing_db_leads = leads_res.scalars().all()

    if existing_db_leads:
        return {
            "status": "success",
            "case_id": case_id,
            "total_leads": len(existing_db_leads),
            "leads": [
                {
                    "lead_id": l.id,
                    "case_id": l.case_id,
                    "title": l.title,
                    "priority": l.priority or "MEDIUM",
                    "summary": l.summary,
                    "confidence": l.confidence,
                    "supporting_evidence": l.supporting_evidence_ids or [],
                    "supporting_findings": l.supporting_findings or [],
                    "reasoning_factors": l.reasoning_factors or (l.reasoning_chain if isinstance(l.reasoning_chain, list) else []),
                    "recommended_next_action": l.next_recommended_actions or [],
                    "status": l.status.value if hasattr(l.status, "value") else str(l.status),
                    "disclaimer": getattr(l, "disclaimer", LEAD_DISCLAIMER_TEXT)
                }
                for l in existing_db_leads
            ],
            "disclaimer": LEAD_DISCLAIMER_TEXT
        }

    # 3. If no DB leads, compute via LeadEngine
    ev_res = await db.execute(select(Evidence).filter(Evidence.case_id == case_id))
    evidence_items = ev_res.scalars().all()
    ev_list = [{"id": e.id, "file_name": e.file_name, "file_type": e.file_type} for e in evidence_items]

    finding_res = await db.execute(select(Finding).filter(Finding.case_id == case_id))
    findings = finding_res.scalars().all()
    raw_findings = [{"id": f.id, "evidence_id": f.evidence_id, "tool_name": f.tool_name, "content": f.content} for f in findings]

    synthetic_dir = "./data/synthetic_cases/case_001" if os.path.exists("./data/synthetic_cases/case_001") else None

    # Compute graph & timeline & gaps
    nodes = IntelligenceFusionService.resolve_entities(raw_findings, ev_list)
    fusion_results = IntelligenceFusionService.detect_relationships_and_correlations(raw_findings, ev_list, nodes)
    timeline_results = TimelineEngine.build_timeline(ev_list, raw_findings, synthetic_dir)
    gap_results = GapContradictionEngine.analyze_case(case_id, ev_list, raw_findings, synthetic_dir)

    generated_leads = LeadEngine.generate_leads(
        case_id=case_id,
        findings=raw_findings,
        relationships=fusion_results["edges"],
        timeline_events=timeline_results["timeline"],
        evidence_gaps=gap_results["evidence_gaps"],
        contradictions=gap_results["contradictions"],
        evidence_items=ev_list
    )

    for l in generated_leads:
        l_dict = l.model_dump() if hasattr(l, "model_dump") else l.dict()
        target_id = l_dict.get("lead_id") or l_dict.get("id") or str(uuid.uuid4())
        lead_db = Lead(
            id=target_id,
            case_id=case_id,
            title=l_dict.get("title"),
            summary=l_dict.get("summary"),
            priority=l_dict.get("priority", "MEDIUM"),
            status=LeadStatus.PENDING_REVIEW,
            confidence=l_dict.get("confidence", 0.85),
            supporting_evidence_ids=l_dict.get("supporting_evidence", []),
            supporting_findings=l_dict.get("supporting_findings", []),
            reasoning_factors=l_dict.get("reasoning_factors", []),
            next_recommended_actions=l_dict.get("recommended_next_action", []),
            disclaimer=l_dict.get("disclaimer", LEAD_DISCLAIMER_TEXT)
        )
        db.add(lead_db)

    await db.commit()

    # Re-fetch persisted DB leads to guarantee 100% ID consistency
    leads_res = await db.execute(select(Lead).filter(Lead.case_id == case_id).order_by(Lead.created_at.desc()))
    persisted_leads = leads_res.scalars().all()

    return {
        "status": "success",
        "case_id": case_id,
        "total_leads": len(persisted_leads),
        "leads": [
            {
                "id": l.id,
                "lead_id": l.id,
                "case_id": l.case_id,
                "title": l.title,
                "priority": l.priority or "MEDIUM",
                "summary": l.summary,
                "confidence": l.confidence,
                "supporting_evidence": l.supporting_evidence_ids or [],
                "supporting_findings": l.supporting_findings or [],
                "reasoning_factors": l.reasoning_factors or [],
                "recommended_next_action": l.next_recommended_actions or [],
                "status": l.status.value if hasattr(l.status, "value") else str(l.status),
                "disclaimer": getattr(l, "disclaimer", LEAD_DISCLAIMER_TEXT)
            }
            for l in persisted_leads
        ],
        "disclaimer": LEAD_DISCLAIMER_TEXT
    }
