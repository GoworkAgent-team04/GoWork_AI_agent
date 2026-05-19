from typing import Any, Dict, List, Optional

from sqlalchemy import text

from backend.config import config
from backend.database.connection import get_db


def search_jobs(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    조건에 맞는 일자리 목록을 반환합니다.

    params:
        region         : 지역 (시/구/원문 ILIKE)
        job_type       : 직종 키워드 (title_raw ILIKE)
        physical_limit : True면 LOW/MID 공고만 조회
    """
    with get_db() as db:
        query = """
            SELECT
                jp.id, jp.title_raw, jp.company_raw,
                jp.location_city, jp.location_district, jp.location_raw,
                jp.job_category_norm, jp.work_type_norm, jp.work_type_raw,
                jp.salary_raw, jp.salary_min, jp.salary_max, jp.salary_type_norm,
                jp.schedule_raw, jp.physical_level, jp.senior_tag,
                jp.age_min, jp.age_max, jp.source_url,
                jp.deadline_at, jp.deadline_type
            FROM job_posting jp
            WHERE 1=1
        """
        query_params: Dict[str, Any] = {}

        if params.get("region"):
            query += """
                AND (
                    jp.location_city     ILIKE :region
                    OR jp.location_district ILIKE :region
                    OR jp.location_raw      ILIKE :region
                )
            """
            query_params["region"] = f"%{params['region']}%"

        if params.get("job_type"):
            query += " AND jp.title_raw ILIKE :job_type"
            query_params["job_type"] = f"%{params['job_type']}%"

        if params.get("physical_limit") is True:
            query += " AND (jp.physical_level IN ('LOW', 'MID') OR jp.physical_level IS NULL)"

        query += " ORDER BY jp.collected_at DESC LIMIT :limit"
        query_params["limit"] = config.JOB_CANDIDATE_POOL

        result = db.execute(text(query), query_params)
        return [dict(row._mapping) for row in result]


def find_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """특정 공고의 상세 정보를 반환합니다."""
    with get_db() as db:
        row = db.execute(
            text("""
                SELECT jp.*, jc.phone_type, jc.department
                FROM job_posting jp
                LEFT JOIN job_contact jc ON jc.posting_id = jp.id
                WHERE jp.id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()
        return dict(row._mapping) if row else None


def find_job_source_url(job_id: str) -> Optional[str]:
    """공고 원본 URL을 반환합니다."""
    with get_db() as db:
        row = db.execute(
            text("SELECT source_url FROM job_posting WHERE id = :job_id"),
            {"job_id": job_id},
        ).fetchone()
        return row.source_url if row else None
