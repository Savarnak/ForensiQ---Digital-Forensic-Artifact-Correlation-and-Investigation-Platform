from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.evidence import EvidenceResponse
from app.services.evidence_service import EvidenceService

router = APIRouter(tags=["Evidence Ingestion"])

@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: str,
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await EvidenceService.upload_evidence(db, case_id, file_type, file)

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_case_evidence(case_id: str, db: AsyncSession = Depends(get_db)):
    return await EvidenceService.get_evidence_by_case(db, case_id)
