from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from typing import List

from app.models.case import Case
from app.models.goal import InvestigationGoal
from app.models.audit import AuditEvent
from app.schemas.goal import InvestigationGoalCreate

class GoalService:
    @staticmethod
    async def create_goal(
        db: AsyncSession,
        case_id: str,
        payload: InvestigationGoalCreate
    ) -> InvestigationGoal:
        case_res = await db.execute(select(Case).filter(Case.id == case_id))
        if not case_res.scalars().first():
            raise HTTPException(status_code=404, detail="Target case not found.")

        goal = InvestigationGoal(
            case_id=case_id,
            goal_text=payload.goal_text,
            priority=payload.priority or "MEDIUM",
            status="PENDING"
        )
        db.add(goal)

        audit = AuditEvent(
            case_id=case_id,
            event_type="GOAL_ADDED",
            actor="INVESTIGATOR",
            details={"goal_text": payload.goal_text, "priority": payload.priority}
        )
        db.add(audit)

        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def get_goals_by_case(db: AsyncSession, case_id: str) -> List[InvestigationGoal]:
        result = await db.execute(select(InvestigationGoal).filter(InvestigationGoal.case_id == case_id).order_by(InvestigationGoal.created_at.desc()))
        return result.scalars().all()
