from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from backend.config import config
from backend.database.connection import get_db
from backend.models.orm import JobContact, JobPosting


def search_jobs(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    조건에 맞는 일자리 목록을 반환합니다.

    Hard Filter:
        region         : 지역 (시/구/원문 ILIKE)
        physical_limit : True면 LOW/MID 공고만 조회

    job_type은 Soft Scoring에서만 사용 (Hard Filter 제외)
    """
    with get_db() as db:
        q = db.query(JobPosting)

        if params.get("region"):
            region = f"%{params['region']}%"
            q = q.filter(
                or_(
                    JobPosting.location_city.ilike(region),
                    JobPosting.location_district.ilike(region),
                    JobPosting.location_raw.ilike(region),
                )
            )

        if params.get("physical_limit") is True:
            q = q.filter(
                or_(
                    JobPosting.physical_level.in_(["LOW", "MID"]),
                    JobPosting.physical_level.is_(None),
                )
            )

        postings = q.order_by(JobPosting.collected_at.desc()).limit(config.JOB_CANDIDATE_POOL).all()
        return [_posting_to_dict(p) for p in postings]


def find_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """특정 공고의 상세 정보를 반환합니다."""
    with get_db() as db:
        posting = db.get(JobPosting, job_id)
        if not posting:
            return None
        contact = db.query(JobContact).filter(JobContact.posting_id == job_id).first()
        result = _posting_to_dict(posting)
        if contact:
            result["phone_type"] = contact.phone_type
            result["department"] = contact.department
        return result


def find_job_source_url(job_id: str) -> Optional[str]:
    """공고 원본 URL을 반환합니다."""
    with get_db() as db:
        posting = db.get(JobPosting, job_id)
        return posting.source_url if posting else None


def _posting_to_dict(p: JobPosting) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title_raw": p.title_raw,
        "company_raw": p.company_raw,
        "location_city": p.location_city,
        "location_district": p.location_district,
        "location_raw": p.location_raw,
        "job_category_norm": p.job_category_norm,
        "work_type_norm": p.work_type_norm,
        "work_type_raw": p.work_type_raw,
        "salary_raw": p.salary_raw,
        "salary_min": p.salary_min,
        "salary_max": p.salary_max,
        "salary_type_norm": p.salary_type_norm,
        "schedule_raw": p.schedule_raw,
        "physical_level": p.physical_level,
        "senior_tag": p.senior_tag,
        "age_min": p.age_min,
        "age_max": p.age_max,
        "source_url": p.source_url,
        "deadline_at": p.deadline_at,
        "deadline_type": p.deadline_type,
    }
