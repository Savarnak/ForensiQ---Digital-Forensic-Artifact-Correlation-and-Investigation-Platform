from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.goal import InvestigationGoalCreate, InvestigationGoalResponse
from app.services.goal_service import GoalService

router = APIRouter(tags=["Investigation Goals"])

@router.post("/cases/{case_id}/goals", response_model=InvestigationGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    case_id: str,
    payload: InvestigationGoalCreate,
    db: AsyncSession = Depends(get_db)
):
    return await GoalService.create_goal(db, case_id, payload)

@router.get("/cases/{case_id}/goals", response_model=List[InvestigationGoalResponse])
async def list_goals(case_id: str, db: AsyncSession = Depends(get_db)):
    return await GoalService.get_goals_by_case(db, case_id)
