from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import NeonDatabase
from backend.database.repositories.session_repo import SessionRepository
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class CreateSessionRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = {}

class UpdateSessionRequest(BaseModel):
    metadata: Dict[str, Any]

@router.post("")
async def create_session(request: CreateSessionRequest, db: AsyncSession = Depends(NeonDatabase.get_session)):
    repo = SessionRepository(db)
    session = await repo.create_session(metadata=request.metadata)
    return {"session_id": str(session.id), "created_at": session.created_at}

@router.get("/{session_id}")
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(NeonDatabase.get_session)):
    repo = SessionRepository(db)
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": str(session.id),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "metadata": session.metadata_
    }

@router.patch("/{session_id}")
async def update_session(session_id: uuid.UUID, request: UpdateSessionRequest, db: AsyncSession = Depends(NeonDatabase.get_session)):
    repo = SessionRepository(db)
    session = await repo.update_session(session_id, request.metadata)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": str(session.id),
        "updated_at": session.updated_at,
        "metadata": session.metadata_
    }
