from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.models.lead import Lead, LeadStatus, LEAD_DISCLAIMER_TEXT
from app.models.audit import AuditEvent
from app.core.logging import logger

router = APIRouter(prefix="/leads", tags=["Leads & Human-in-the-Loop Review"])

class HumanReviewPayload(BaseModel):
    investigator_id: str = Field(..., json_schema_extra={"example": "OFFICER-7781"})
    reason: Optional[str] = Field(None, json_schema_extra={"example": "Geotag cross-reference verified with cell tower CDR logs."})

class LeadResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    title: str
    summary: str
    priority: str
    status: str
    confidence: float
    supporting_evidence_ids: List[Any]
    supporting_findings: List[Any]
    reasoning_factors: List[Any]
    reasoning_chain: List[Any]
    next_recommended_actions: List[Any]
    disclaimer: str
    provenance_type: str = "HUMAN_INVESTIGATOR_DECISION"
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewer_notes: Optional[str]

@router.get("/case/{case_id}", response_model=List[LeadResponseSchema])
async def list_case_leads(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).filter(Lead.case_id == case_id).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    out = []
    for l in leads:
        st = l.status.value if hasattr(l.status, "value") else str(l.status)
        prov = "HUMAN_INVESTIGATOR_DECISION" if l.reviewed_at else "AI_GENERATED_RECOMMENDATION"
        out.append(LeadResponseSchema(
            id=l.id,
            case_id=l.case_id,
            title=l.title,
            summary=l.summary,
            priority=l.priority or "MEDIUM",
            status=st,
            confidence=l.confidence,
            supporting_evidence_ids=l.supporting_evidence_ids or [],
            supporting_findings=l.supporting_findings or [],
            reasoning_factors=l.reasoning_factors or [],
            reasoning_chain=l.reasoning_chain or [],
            next_recommended_actions=l.next_recommended_actions or [],
            disclaimer=getattr(l, "disclaimer", LEAD_DISCLAIMER_TEXT),
            provenance_type=prov,
            created_at=l.created_at,
            reviewed_at=l.reviewed_at,
            reviewed_by=l.reviewed_by,
            reviewer_notes=l.reviewer_notes
        ))
    return out

async def _process_human_decision(
    lead_id: str,
    new_status_enum: LeadStatus,
    action_label: str,
    payload: HumanReviewPayload,
    db: AsyncSession
) -> LeadResponseSchema:
    """Helper method to process human investigator decision and record an immutable AuditEvent."""
    result = await db.execute(select(Lead).filter(Lead.id == lead_id))
    lead = result.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found.")

    prev_status = lead.status.value if hasattr(lead.status, "value") else str(lead.status)
    new_status = new_status_enum.value

    # Update Lead state
    lead.status = new_status_enum
    lead.reviewed_at = datetime.utcnow()
    lead.reviewed_by = payload.investigator_id
    lead.reviewer_notes = payload.reason

    # Create Immutable AuditEvent Record
    audit_event = AuditEvent(
        case_id=lead.case_id,
        event_type=f"LEAD_{action_label}",
        actor=payload.investigator_id,
        details={
            "lead_id": lead.id,
            "investigator_id": payload.investigator_id,
            "action": action_label,
            "timestamp": lead.reviewed_at.isoformat(),
            "previous_status": prev_status,
            "new_status": new_status,
            "reason": payload.reason or "No reason specified",
            "provenance": "HUMAN_INVESTIGATOR_DECISION"
        }
    )
    db.add(audit_event)

    await db.commit()
    await db.refresh(lead)

    logger.info(f"[Human-in-the-Loop] Lead {lead_id} status transitioned from {prev_status} -> {new_status} by {payload.investigator_id}")

    return LeadResponseSchema(
        id=lead.id,
        case_id=lead.case_id,
        title=lead.title,
        summary=lead.summary,
        priority=lead.priority or "MEDIUM",
        status=new_status,
        confidence=lead.confidence,
        supporting_evidence_ids=lead.supporting_evidence_ids or [],
        supporting_findings=lead.supporting_findings or [],
        reasoning_factors=lead.reasoning_factors or [],
        reasoning_chain=lead.reasoning_chain or [],
        next_recommended_actions=lead.next_recommended_actions or [],
        disclaimer=getattr(lead, "disclaimer", LEAD_DISCLAIMER_TEXT),
        provenance_type="HUMAN_INVESTIGATOR_DECISION",
        created_at=lead.created_at,
        reviewed_at=lead.reviewed_at,
        reviewed_by=lead.reviewed_by,
        reviewer_notes=lead.reviewer_notes
    )

@router.post("/{lead_id}/approve", response_model=LeadResponseSchema)
async def approve_lead(lead_id: str, payload: HumanReviewPayload, db: AsyncSession = Depends(get_db)):
    """POST /api/leads/{lead_id}/approve - Human investigator approves candidate lead."""
    return await _process_human_decision(lead_id, LeadStatus.APPROVED, "APPROVED", payload, db)

@router.post("/{lead_id}/reject", response_model=LeadResponseSchema)
async def reject_lead(lead_id: str, payload: HumanReviewPayload, db: AsyncSession = Depends(get_db)):
    """POST /api/leads/{lead_id}/reject - Human investigator rejects candidate lead."""
    return await _process_human_decision(lead_id, LeadStatus.REJECTED, "REJECTED", payload, db)

@router.post("/{lead_id}/request-analysis", response_model=LeadResponseSchema)
async def request_analysis_lead(lead_id: str, payload: HumanReviewPayload, db: AsyncSession = Depends(get_db)):
    """POST /api/leads/{lead_id}/request-analysis - Human investigator requests further analysis."""
    return await _process_human_decision(lead_id, LeadStatus.NEEDS_MORE_ANALYSIS, "NEEDS_MORE_ANALYSIS", payload, db)

@router.patch("/{lead_id}/review", response_model=LeadResponseSchema)
async def review_lead_legacy(lead_id: str, payload: HumanReviewPayload, db: AsyncSession = Depends(get_db)):
    """Legacy PATCH review endpoint."""
    return await _process_human_decision(lead_id, LeadStatus.APPROVED, "APPROVED", payload, db)
