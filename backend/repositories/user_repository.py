from typing import Any, Dict, List, Optional

from sqlalchemy import text

from backend.database.connection import get_db


def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """users 테이블에서 기본 정보를 조회합니다."""
    with get_db() as db:
        row = db.execute(
            text("SELECT id, name, age, phone, address, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()
        return dict(row._mapping) if row else None


def find_careers_by_user_id(user_id: int) -> List[Dict[str, Any]]:
    """유저의 경력 목록을 조회합니다."""
    with get_db() as db:
        rows = db.execute(
            text("""
                SELECT company_name, job_title, start_date, end_date, is_current, description
                FROM careers
                WHERE user_id = :user_id
                ORDER BY start_date DESC
            """),
            {"user_id": user_id},
        ).fetchall()
        return [dict(row._mapping) for row in rows]


def find_certifications_by_user_id(user_id: int) -> List[str]:
    """유저의 자격증 이름 목록을 조회합니다."""
    with get_db() as db:
        rows = db.execute(
            text(
                "SELECT name FROM certifications WHERE user_id = :user_id ORDER BY issued_date DESC"
            ),
            {"user_id": user_id},
        ).fetchall()
        return [row.name for row in rows]


def find_language_skills_by_user_id(user_id: int) -> List[Dict[str, str]]:
    """유저의 어학 능력 목록을 조회합니다."""
    with get_db() as db:
        rows = db.execute(
            text("SELECT language, level FROM language_skills WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchall()
        return [dict(row._mapping) for row in rows]


def find_document_skills_by_user_id(user_id: int) -> List[str]:
    """유저의 문서 툴 목록을 조회합니다."""
    with get_db() as db:
        rows = db.execute(
            text("SELECT tool FROM document_skills WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchall()
        return [row.tool for row in rows]


def find_other_skills_by_user_id(user_id: int) -> List[str]:
    """유저의 기타 역량 키워드 목록을 조회합니다."""
    with get_db() as db:
        rows = db.execute(
            text("SELECT keyword FROM other_skills WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchall()
        return [row.keyword for row in rows]
