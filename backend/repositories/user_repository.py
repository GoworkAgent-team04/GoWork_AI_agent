from typing import Any, Dict, List, Optional

from backend.database.connection import get_db
from backend.models.orm import Career, Certification, DocumentSkill, LanguageSkill, OtherSkill, User


def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """users 테이블에서 기본 정보를 조회합니다."""
    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return None
        return {
            "id": user.id,
            "name": user.name,
            "age": user.age,
            "phone": user.phone,
            "address": user.address,
            "created_at": user.created_at,
        }


def find_careers_by_user_id(user_id: int) -> List[Dict[str, Any]]:
    """유저의 경력 목록을 조회합니다."""
    with get_db() as db:
        careers = (
            db.query(Career)
            .filter(Career.user_id == user_id)
            .order_by(Career.start_date.desc())
            .all()
        )
        return [
            {
                "company_name": c.company_name,
                "job_title": c.job_title,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "is_current": c.is_current,
                "description": c.description,
            }
            for c in careers
        ]


def find_certifications_by_user_id(user_id: int) -> List[str]:
    """유저의 자격증 이름 목록을 조회합니다."""
    with get_db() as db:
        certs = (
            db.query(Certification)
            .filter(Certification.user_id == user_id)
            .order_by(Certification.issued_date.desc())
            .all()
        )
        return [c.name for c in certs]


def find_language_skills_by_user_id(user_id: int) -> List[Dict[str, str]]:
    """유저의 어학 능력 목록을 조회합니다."""
    with get_db() as db:
        skills = db.query(LanguageSkill).filter(LanguageSkill.user_id == user_id).all()
        return [{"language": s.language, "level": s.level} for s in skills]


def find_document_skills_by_user_id(user_id: int) -> List[str]:
    """유저의 문서 툴 목록을 조회합니다."""
    with get_db() as db:
        skills = db.query(DocumentSkill).filter(DocumentSkill.user_id == user_id).all()
        return [s.tool for s in skills]


def find_other_skills_by_user_id(user_id: int) -> List[str]:
    """유저의 기타 역량 키워드 목록을 조회합니다."""
    with get_db() as db:
        skills = db.query(OtherSkill).filter(OtherSkill.user_id == user_id).all()
        return [s.keyword for s in skills]
