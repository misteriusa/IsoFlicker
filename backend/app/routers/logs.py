"""Session log endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..database import get_session
from ..models import SessionLog
from ..schemas import SessionLogCreate, SessionLogRead

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/", response_model=SessionLogRead, status_code=201)
def create_log(payload: SessionLogCreate, session: Session = Depends(get_session)) -> SessionLogRead:
    """Persist a new session log entry."""

    log = SessionLog(**payload.model_dump())
    session.add(log)
    session.commit()
    session.refresh(log)
    return SessionLogRead.model_validate(log)


@router.get("/", response_model=list[SessionLogRead])
def list_logs(session: Session = Depends(get_session)) -> list[SessionLogRead]:
    """Return session logs ordered by newest first."""

    logs = session.exec(select(SessionLog).order_by(SessionLog.started_at.desc())).all()
    return [SessionLogRead.model_validate(item) for item in logs]


__all__ = ["router"]
