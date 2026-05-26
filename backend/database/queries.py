"""
DB 쿼리 함수 모음.

실제 테이블 스키마 기준:
  - job_posting  : 일자리 공고 (id: uuid)
  - job_contact  : 공고 연락처
  - job_platform : 공고 출처 플랫폼
  - collection_log: 수집 로그
  - users        : 사용자 프로필 (임시)
  - applications : 지원 이력
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import text

from backend.config import config
from backend.database.connection import get_db

# ─── 직종 한글 → DB enum 매핑 ────────────────────────────────────
# LLM이 추출한 한글 직종명을 job_category_norm enum 값으로 변환

JOB_CATEGORY_MAP: Dict[str, str] = {
    # SECURITY
    "경비": "SECURITY",
    "보안": "SECURITY",
    "시설관리": "SECURITY",
    # CLEANING
    "청소": "CLEANING",
    "환경미화": "CLEANING",
    "청결": "CLEANING",
    # CARE
    "요양": "CARE",
    "돌봄": "CARE",
    "케어": "CARE",
    "간병": "CARE",
    "요양보호사": "CARE",
    "복지": "CARE",
    # KITCHEN
    "주방": "KITCHEN",
    "조리": "KITCHEN",
    "요리": "KITCHEN",
    "식당": "KITCHEN",
    "조리사": "KITCHEN",
    # DRIVING
    "운전": "DRIVING",
    "드라이버": "DRIVING",
    "기사": "DRIVING",
    # SALES
    "판매": "SALES",
    "영업": "SALES",
    "매장": "SALES",
    # OFFICE
    "사무": "OFFICE",
    "행정": "OFFICE",
    "총무": "OFFICE",
    # PRODUCTION
    "생산": "PRODUCTION",
    "제조": "PRODUCTION",
    "공장": "PRODUCTION",
    # DELIVERY
    "배달": "DELIVERY",
    "배송": "DELIVERY",
    "택배": "DELIVERY",
    # COUNSELING
    "상담": "COUNSELING",
    # ENVIRONMENT
    "환경": "ENVIRONMENT",
}


def _map_job_category(job_type: str) -> Optional[str]:
    """한글 직종명을 DB enum 값으로 변환합니다."""
    job_type_lower = job_type.strip()
    for keyword, category in JOB_CATEGORY_MAP.items():
        if keyword in job_type_lower:
            return category
    return None  # 매핑 실패 시 title_raw 검색으로 폴백


# ─── 일자리 검색 ─────────────────────────────────────────────────


def search_jobs(params: Dict[str, Any]) -> List[Dict]:
    """
    조건에 맞는 활성 일자리 목록을 반환합니다.

    params 예시:
        {
            "region"        : "서울",
            "job_type"      : "경비",        # 한글 직종명
            "physical_limit": True,          # 신체 제약 여부
            "work_type"     : "PART_TIME",
            "salary_min"    : 1500000,
        }

    컬럼 매핑:
        region         → location_city / location_district / location_raw
        job_type       → job_category_norm (enum 변환) → 실패 시 title_raw ILIKE
        physical_limit → physical_level (True면 LOW/MID만, False면 전체)
        work_type      → work_type_norm
        salary_min     → salary_min
    """
    with get_db() as db:
        # ── 현재 DB 상태 ──────────────────────────────────────────────
        # status_norm   : 전부 UNKNOWN (정규화 미완료) → 필터 제거
        # job_category_norm : 전부 NULL               → title_raw ILIKE 폴백
        # work_type_norm    : 전부 NULL               → 필터 스킵
        # salary_min        : 전부 NULL               → 필터 스킵
        # location_city/district : 정상 수집됨        → 지역 검색 가능
        query = """
            SELECT
                jp.id,
                jp.title_raw,
                jp.company_raw,
                jp.location_city,
                jp.location_district,
                jp.location_raw,
                jp.job_category_norm,
                jp.work_type_norm,
                jp.work_type_raw,
                jp.salary_raw,
                jp.salary_min,
                jp.salary_max,
                jp.salary_type_norm,
                jp.schedule_raw,
                jp.physical_level,
                jp.senior_tag,
                jp.age_min,
                jp.age_max,
                jp.source_url,
                jp.deadline_at,
                jp.deadline_type
            FROM job_posting jp
            WHERE 1=1
        """
        query_params: Dict[str, Any] = {}

        # 지역 검색 (시/구/원문 모두 검색)
        if params.get("region"):
            query += """
                AND (
                    jp.location_city     ILIKE :region
                    OR jp.location_district ILIKE :region
                    OR jp.location_raw      ILIKE :region
                )
            """
            query_params["region"] = f"%{params['region']}%"

        # 직종 검색
        # job_category_norm이 NULL이므로 title_raw ILIKE로만 검색
        if params.get("job_category_list"):
            # 파라미터 완화 재검색: 여러 키워드 OR 조건으로 title_raw 검색
            keyword_conditions = " OR ".join(
                f"jp.title_raw ILIKE :kw_{i}" for i in range(len(params["job_category_list"]))
            )
            query += f" AND ({keyword_conditions})"
            # enum값(SECURITY 등)을 다시 한글 키워드로 역매핑
            _CATEGORY_TO_KW = {
                "SECURITY": "경비",
                "CLEANING": "미화",
                "CARE": "요양",
                "KITCHEN": "주방",
                "DRIVING": "운전",
                "DELIVERY": "배송",
                "SALES": "판매",
                "OFFICE": "사무",
                "PRODUCTION": "생산",
                "ENVIRONMENT": "환경",
                "COUNSELING": "상담",
            }
            for i, cat in enumerate(params["job_category_list"]):
                kw = _CATEGORY_TO_KW.get(cat, cat.lower())
                query_params[f"kw_{i}"] = f"%{kw}%"

        elif params.get("job_type"):
            # title_raw 키워드 검색
            query += " AND jp.title_raw ILIKE :job_type"
            query_params["job_type"] = f"%{params['job_type']}%"

        # 신체 제약 필터 (physical_level이 NULL이면 스킵)
        if params.get("physical_limit") is True:
            query += " AND (jp.physical_level IN ('LOW', 'MID') OR jp.physical_level IS NULL)"

        # 근무 형태 / 급여 필터는 해당 컬럼이 NULL이므로 현재 스킵

        query += f" ORDER BY jp.collected_at DESC LIMIT {config.MAX_JOB_RESULTS}"

        result = db.execute(text(query), query_params)
        return [dict(row._mapping) for row in result]


# ─── 공고 상세 조회 ───────────────────────────────────────────────


def get_job_detail(job_id: str) -> Optional[Dict]:
    """
    특정 공고의 상세 정보를 반환합니다.

    Args:
        job_id: 공고 UUID (문자열)
    """
    with get_db() as db:
        result = db.execute(
            text("""
                SELECT
                    jp.*,
                    jc.phone_type,
                    jc.department
                FROM job_posting jp
                LEFT JOIN job_contact jc ON jc.posting_id = jp.id
                WHERE jp.id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()
        return dict(result._mapping) if result else None


# ─── 지원 처리 ────────────────────────────────────────────────────


def apply_to_job(user_id: str, job_id: str) -> dict:
    """
    지원 처리합니다.

    Returns:
        {
            "success" : bool  - 지원 성공 여부
            "duplicate": bool - 중복 지원 여부
        }
    """
    with get_db() as db:
        # 중복 지원 체크
        existing = db.execute(
            text(
                "SELECT 1 FROM applications "
                "WHERE user_id = :user_id AND posting_id = :posting_id"
            ),
            {"user_id": user_id, "posting_id": job_id},
        ).fetchone()

        if existing:
            return {"success": False, "duplicate": True}

        try:
            db.execute(
                text(
                    "INSERT INTO applications (user_id, posting_id, status) "
                    "VALUES (:user_id, :posting_id, 'PENDING')"
                ),
                {"user_id": user_id, "posting_id": job_id},
            )
            db.commit()
            return {"success": True, "duplicate": False}
        except Exception:
            db.rollback()
            return {"success": False, "duplicate": False}


def get_job_source_url(job_id: str) -> Optional[str]:
    """공고 원본 URL을 반환합니다. (지원 링크로 활용)"""
    with get_db() as db:
        result = db.execute(
            text("SELECT source_url FROM job_posting WHERE id = :job_id"),
            {"job_id": job_id},
        ).fetchone()
        return result.source_url if result else None


def get_user_applications(user_id: str) -> List[Dict]:
    """사용자의 지원 이력을 반환합니다."""
    with get_db() as db:
        result = db.execute(
            text("""
                SELECT
                    a.id,
                    a.status,
                    a.applied_at,
                    jp.title_raw,
                    jp.company_raw,
                    jp.location_city
                FROM applications a
                JOIN job_posting jp ON jp.id = a.posting_id
                WHERE a.user_id = :user_id
                ORDER BY a.applied_at DESC
            """),
            {"user_id": user_id},
        )
        return [dict(row._mapping) for row in result]


# ─── 사용자 프로필 ────────────────────────────────────────────────


def get_user_profile(user_id: str) -> Optional[Dict]:
    """사용자 프로필을 반환합니다."""
    with get_db() as db:
        result = db.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()
        return dict(result._mapping) if result else None


# 모듈 로드 시 허용된 컬럼별 쿼리를 미리 빌드 (런타임에 컬럼명 삽입 없음)
_ALLOWED_UPDATE_FIELDS = {
    "region_city",
    "region_district",
    "preferred_job_category",
    "preferred_work_type",
    "physical_level",
    "career_type",
    "experience_desc",
}
_UPDATE_QUERIES = {
    field: text(f"UPDATE users SET {field} = :value, updated_at = now() WHERE id = :user_id")
    for field in _ALLOWED_UPDATE_FIELDS
}


def update_user_profile(user_id: str, field: str, value: Any) -> bool:
    """사용자 프로필의 특정 필드를 수정합니다."""
    query = _UPDATE_QUERIES.get(field)
    if query is None:
        return False

    with get_db() as db:
        try:
            db.execute(query, {"value": value, "user_id": user_id})
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
