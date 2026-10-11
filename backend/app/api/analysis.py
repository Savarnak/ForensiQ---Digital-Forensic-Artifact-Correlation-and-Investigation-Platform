from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import os

from app.core.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.evidence.gap_contradiction_engine import GapContradictionEngine
from app.core.logging import logger

router = APIRouter(prefix="/cases", tags=["Evidence Gap & Contradiction Engine"])

@router.get("/{case_id}/analysis/gaps-contradictions")
async def get_case_gaps_and_contradictions(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    GET /api/cases/{case_id}/analysis/gaps-contradictions
    Returns evidence gap analysis, timestamp/attribute contradictions, incomplete investigation chains,
    confidence scores, supporting evidence citations, and investigator non-guilt disclaimers.
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

    # 5. Execute Gap & Contradiction Analysis
    logger.info(f"Executing ARGUS Evidence Gap & Contradiction Engine for Case {case_obj.case_number}...")
    analysis_result = GapContradictionEngine.analyze_case(
        case_id=case_id,
        evidence_items=ev_list,
        raw_findings=raw_findings,
        synthetic_case_dir=synthetic_dir
    )

    return analysis_result
