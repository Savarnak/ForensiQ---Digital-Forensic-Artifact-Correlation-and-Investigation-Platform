from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional
import uuid

from app.models.case import Case
from app.models.run import InvestigationRun
from app.models.audit import AuditEvent
from app.schemas.investigation import InvestigationRunCreate

class InvestigationService:
    @staticmethod
    async def create_investigation_run(
        db: AsyncSession,
        case_id: str,
        payload: Optional[InvestigationRunCreate] = None
    ) -> InvestigationRun:
        case_res = await db.execute(select(Case).filter(Case.id == case_id))
        case_obj = case_res.scalars().first()
        if not case_obj:
            raise HTTPException(status_code=404, detail="Target case not found.")

        goal_id = payload.goal_id if payload else None
        run_id = str(uuid.uuid4())

        new_run = InvestigationRun(
            id=run_id,
            case_id=case_id,
            goal_id=goal_id,
            status="PENDING",
            summary=f"Investigation run initialized for Case {case_obj.case_number}"
        )
        db.add(new_run)

        audit = AuditEvent(
            case_id=case_id,
            event_type="INVESTIGATION_INITIALIZED",
            actor="ARGUS_SYSTEM",
            details={"run_id": run_id, "goal_id": goal_id}
        )
        db.add(audit)

        await db.commit()

        # Re-fetch with eager loaded tasks
        res = await db.execute(
            select(InvestigationRun)
            .options(selectinload(InvestigationRun.tasks))
            .filter(InvestigationRun.id == run_id)
        )
        return res.scalars().first()

    @staticmethod
    async def get_investigation_runs_by_case(
        db: AsyncSession,
        case_id: str
    ) -> List[InvestigationRun]:
        result = await db.execute(
            select(InvestigationRun)
            .options(selectinload(InvestigationRun.tasks))
            .filter(InvestigationRun.case_id == case_id)
            .order_by(InvestigationRun.created_at.desc())
        )
        return result.scalars().all()
