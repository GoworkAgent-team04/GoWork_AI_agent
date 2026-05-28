from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.database.connection import get_db
from backend.models.orm import ChatMessage, ChatSearchParams, ChatSession


def get_or_create_session(user_id: int) -> int:
    """최신 세션 ID 반환. 없으면 새 세션 생성."""
    with get_db() as db:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .first()
        )
        if session:
            return session.id
        new_session = ChatSession(user_id=user_id)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session.id


def create_session(user_id: int) -> int:
    """새 세션 생성 후 ID 반환 (대화 초기화 시 사용)."""
    with get_db() as db:
        new_session = ChatSession(user_id=user_id)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session.id


def save_message(
    session_id: int,
    role: str,
    content: str,
    job_ids: Optional[List[str]] = None,
) -> None:
    """메시지를 DB에 저장합니다."""
    with get_db() as db:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            job_ids=job_ids or None,
        )
        db.add(msg)
        db.query(ChatSession).filter(ChatSession.id == session_id).update(
            {"updated_at": datetime.now()},
            synchronize_session=False,
        )
        db.commit()


def save_search_params(
    session_id: int,
    user_id: int,
    params: Dict[str, Any],
) -> None:
    """LLM이 추출한 검색 파라미터를 DB에 저장합니다."""
    with get_db() as db:
        row = ChatSearchParams(
            session_id=session_id,
            user_id=user_id,
            region=params.get("region"),
            job_type=params.get("job_type"),
            work_type=str(params["work_type"]) if params.get("work_type") else None,
            physical_limit=params.get("physical_limit"),
            salary_min=params.get("salary_min"),
        )
        db.add(row)
        db.commit()


def get_recent_messages(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """최근 세션의 메시지 목록을 반환합니다."""
    with get_db() as db:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .first()
        )
        if not session:
            return []
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "job_ids": m.job_ids or [],
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
