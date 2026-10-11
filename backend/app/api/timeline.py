from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import os

from app.core.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.evidence.timeline_engine import TimelineEngine
from app.core.logging import logger

router = APIRouter(prefix="/cases", tags=["Timeline Engine"])

@router.get("/{case_id}/timeline")
async def get_case_timeline(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    GET /api/cases/{case_id}/timeline
    Returns a chronological investigation timeline merging chats, calls, GPS, images, metadata, and reports,
    along with detected temporal overlaps, suspicious gaps, conflicting timestamps, and event explanations.
    """
    # 1. Fetch Case
    case_res = await db.execute(select(Case).filter(Case.id == case_id))
    case_obj = case_res.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Target case not found.")

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

    # 3. Fetch Findings
    finding_res = await db.execute(select(Finding).filter(Finding.case_id == case_id))
    findings = finding_res.scalars().all()
    raw_findings = [
        {
            "id": f.id,
            "evidence_id": f.evidence_id,
            "tool_name": f.tool_name,
            "finding_type": f.finding_type,
            "content": f.content,
            "confidence": f.confidence,
            "provenance": f.provenance
        }
        for f in findings
    ]

    # 4. Check for synthetic case directory
    synthetic_dir = "./data/synthetic_cases/case_001"
    if not os.path.exists(synthetic_dir):
        synthetic_dir = None

    # 5. Build Timeline
    logger.info(f"Building ARGUS investigation timeline for Case {case_obj.case_number}...")
    timeline_result = TimelineEngine.build_timeline(
        evidence_items=ev_list,
        raw_findings=raw_findings,
        synthetic_case_dir=synthetic_dir
    )

    return {
        "status": "success",
        "case_id": case_id,
        "case_number": case_obj.case_number,
        "title": case_obj.title,
        "total_events": timeline_result["total_events"],
        "timeline": timeline_result["timeline"],
        "temporal_overlaps": timeline_result["temporal_overlaps"],
        "suspicious_gaps": timeline_result["suspicious_gaps"],
        "conflicting_timestamps": timeline_result["conflicting_timestamps"],
        "analysis_summary": timeline_result["analysis_summary"]
    }
