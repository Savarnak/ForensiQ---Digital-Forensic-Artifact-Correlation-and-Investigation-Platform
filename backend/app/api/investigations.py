from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.schemas.investigation import InvestigationRunCreate, InvestigationRunResponse
from app.services.investigation_service import InvestigationService

router = APIRouter(tags=["Investigation Runs"])

@router.post("/cases/{case_id}/investigations", response_model=InvestigationRunResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation_run(
    case_id: str,
    payload: Optional[InvestigationRunCreate] = None,
    db: AsyncSession = Depends(get_db)
):
    return await InvestigationService.create_investigation_run(db, case_id, payload)

@router.get("/cases/{case_id}/investigations", response_model=List[InvestigationRunResponse])
async def list_investigation_runs(case_id: str, db: AsyncSession = Depends(get_db)):
    return await InvestigationService.get_investigation_runs_by_case(db, case_id)
