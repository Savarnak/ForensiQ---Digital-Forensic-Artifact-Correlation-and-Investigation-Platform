from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from typing import List, Optional
import uuid

from app.models.case import Case, CaseStatus
from app.models.audit import AuditEvent
from app.schemas.case import CaseCreate

class CaseService:
    @staticmethod
    async def create_case(db: AsyncSession, payload: CaseCreate) -> Case:
        existing = await db.execute(select(Case).filter(Case.case_number == payload.case_number))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Case number already exists.")

        case_id = str(uuid.uuid4())
        new_case = Case(
            id=case_id,
            case_number=payload.case_number,
            title=payload.title,
            description=payload.description,
            status=CaseStatus.ACTIVE
        )
        db.add(new_case)

        audit = AuditEvent(
            case_id=case_id,
            event_type="CASE_CREATED",
            actor="INVESTIGATOR",
            details={"case_number": new_case.case_number, "title": new_case.title}
        )
        db.add(audit)

        await db.commit()
        await db.refresh(new_case)
        return new_case

    @staticmethod
    async def list_cases(db: AsyncSession) -> List[Case]:
        result = await db.execute(select(Case).order_by(Case.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_case_by_id(db: AsyncSession, case_id: str) -> Case:
        result = await db.execute(select(Case).filter(Case.id == case_id))
        case_obj = result.scalars().first()
        if not case_obj:
            raise HTTPException(status_code=404, detail="Case not found.")
        return case_obj

    @staticmethod
    async def load_synthetic_case(db: AsyncSession) -> Case:
        import os
        import json
        import hashlib
        from app.models.evidence import Evidence
        from app.models.goal import InvestigationGoal
        from app.core.config import settings
        from app.core.logging import logger

        existing_res = await db.execute(select(Case).filter(Case.case_number == "CASE-2026-CYGNUS"))
        existing_case = existing_res.scalars().first()
        if existing_case:
            ev_check = await db.execute(select(Evidence).filter(Evidence.case_id == existing_case.id))
            if len(ev_check.scalars().all()) >= 4:
                return existing_case
            case_id = existing_case.id
            new_case = existing_case
        else:
            case_id = str(uuid.uuid4())
            new_case = None

        possible_paths = [
            os.path.abspath("./data/synthetic_cases/case_001"),
            os.path.abspath("../data/synthetic_cases/case_001"),
            os.path.join(os.path.dirname(__file__), "../../../data/synthetic_cases/case_001")
        ]
        synthetic_dir = next((p for p in possible_paths if os.path.exists(p)), "./data/synthetic_cases/case_001")
        case_info_path = os.path.join(synthetic_dir, "case.json")

        case_num = "CASE-2026-CYGNUS"
        title = "Operation Cygnus - Online Safety & Evidence Correlation Drill"
        desc = "Synthetic, benign investigation dataset simulating coordinated account handle communications, device geotags, call records, and event timelines for ARGUS architecture demonstration."
        goal_text = "Identify relevant relationships between accounts, devices, locations and events and highlight evidence requiring investigator review."

        if os.path.exists(case_info_path):
            try:
                with open(case_info_path, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    case_num = cdata.get("case_number", case_num)
                    title = cdata.get("title", title)
                    desc = cdata.get("description", desc)
                    goal_text = cdata.get("investigation_goal", goal_text)
            except Exception as e:
                logger.warning(f"Error reading case.json: {e}")

        if new_case is None:
            new_case = Case(
                id=case_id,
                case_number=case_num,
                title=title,
                description=desc,
                status=CaseStatus.ACTIVE
            )
            db.add(new_case)

            audit_case = AuditEvent(
                case_id=case_id,
                event_type="CASE_CREATED",
                actor="INVESTIGATOR",
                details={"case_number": case_num, "title": title, "source": "SYNTHETIC_BENCHMARK_SUITE"}
            )
            db.add(audit_case)

        os.makedirs(settings.EVIDENCE_STORAGE_PATH, exist_ok=True)
        file_type_map = {
            "chats.json": "CHAT_LOG",
            "calls.csv": "CALL_LOG",
            "gps.csv": "GPS_LOG",
            "evidence_photo_01.jpg": "IMAGE",
            "evidence_photo_02.jpg": "IMAGE",
            "screenshot_chat_01.png": "IMAGE",
            "social_messages.json": "SOCIAL_MESSAGE",
            "devices.json": "DEVICE_LOG",
            "events.json": "EVENT_LOG",
        }

        if os.path.exists(synthetic_dir):
            for fname, ftype in file_type_map.items():
                fpath = os.path.join(synthetic_dir, fname)
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        file_bytes = f.read()

                    file_id = str(uuid.uuid4())
                    saved_filename = f"{file_id}_{fname}"
                    saved_filepath = os.path.join(settings.EVIDENCE_STORAGE_PATH, saved_filename)
                    with open(saved_filepath, "wb") as f:
                        f.write(file_bytes)

                    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
                    mime_type = "application/json" if fname.endswith(".json") else ("text/csv" if fname.endswith(".csv") else "image/jpeg")

                    ev_item = Evidence(
                        id=file_id,
                        case_id=case_id,
                        file_name=fname,
                        file_path=saved_filepath,
                        file_type=ftype,
                        mime_type=mime_type,
                        hash_sha256=sha256_hash,
                        file_size_bytes=str(len(file_bytes)),
                        extracted_metadata={}
                    )
                    db.add(ev_item)

                    audit_ev = AuditEvent(
                        case_id=case_id,
                        event_type="EVIDENCE_UPLOADED",
                        actor="INVESTIGATOR",
                        details={"file_name": fname, "file_type": ftype, "sha256": sha256_hash}
                    )
                    db.add(audit_ev)

        goal_obj = InvestigationGoal(
            id=str(uuid.uuid4()),
            case_id=case_id,
            goal_text=goal_text,
            priority="MEDIUM",
            status="ACTIVE"
        )
        db.add(goal_obj)

        audit_goal = AuditEvent(
            case_id=case_id,
            event_type="GOAL_ADDED",
            actor="INVESTIGATOR",
            details={"goal_text": goal_text, "priority": "MEDIUM"}
        )
        db.add(audit_goal)

        await db.commit()
        await db.refresh(new_case)
        return new_case
