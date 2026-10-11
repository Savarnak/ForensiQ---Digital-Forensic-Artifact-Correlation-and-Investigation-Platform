from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, UploadFile
from typing import List
import os
import uuid
import hashlib

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.audit import AuditEvent
from app.core.config import settings

class EvidenceService:
    @staticmethod
    async def upload_evidence(
        db: AsyncSession,
        case_id: str,
        file_type: str,
        file: UploadFile
    ) -> Evidence:
        # Check case existence
        case_res = await db.execute(select(Case).filter(Case.id == case_id))
        if not case_res.scalars().first():
            raise HTTPException(status_code=404, detail="Target case not found.")

        os.makedirs(settings.EVIDENCE_STORAGE_PATH, exist_ok=True)
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}_{file.filename}"
        saved_filepath = os.path.join(settings.EVIDENCE_STORAGE_PATH, saved_filename)

        content = await file.read()
        sha256_hash = hashlib.sha256(content).hexdigest()

        with open(saved_filepath, "wb") as f:
            f.write(content)

        evidence = Evidence(
            id=file_id,
            case_id=case_id,
            file_name=file.filename,
            file_path=saved_filepath,
            file_type=file_type.upper(),
            mime_type=file.content_type,
            hash_sha256=sha256_hash,
            file_size_bytes=str(len(content)),
            extracted_metadata={}
        )
        db.add(evidence)

        audit = AuditEvent(
            case_id=case_id,
            event_type="EVIDENCE_UPLOADED",
            actor="INVESTIGATOR",
            details={"file_name": file.filename, "file_type": file_type, "sha256": sha256_hash}
        )
        db.add(audit)

        await db.commit()
        await db.refresh(evidence)
        return evidence

    @staticmethod
    async def get_evidence_by_case(db: AsyncSession, case_id: str) -> List[Evidence]:
        result = await db.execute(select(Evidence).filter(Evidence.case_id == case_id))
        return result.scalars().all()
