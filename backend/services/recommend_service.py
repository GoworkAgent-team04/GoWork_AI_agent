from typing import Any, Dict, List, Optional

from backend.repositories import job_repository
from backend.schemas.job import JobCard, JobRequestDTO
from backend.scoring import calc_max_score, calc_raw_score, normalize
from backend.scoring.weights import load_weights

TOP_N = 3


def _to_job_card(job: Dict[str, Any]) -> JobCard:
    """DB row → JobCard 변환"""
    location_parts = [job.get("location_city"), job.get("location_district")]
    location = " ".join(p for p in location_parts if p) or job.get("location_raw")

    deadline: Optional[str] = None
    if job.get("deadline_type") == "ALWAYS":
        deadline = "상시모집"
    elif job.get("deadline_at"):
        deadline = str(job["deadline_at"])[:10]

    return JobCard(
        id=str(job["id"]),
        title=job.get("title_raw") or "",
        company=job.get("company_raw"),
        location=location,
        salary=job.get("salary_raw"),
        work_type=job.get("work_type_raw") or job.get("work_type_norm"),
        schedule=job.get("schedule_raw"),
        deadline=deadline,
        source_url=job.get("source_url"),
        physical_level=job.get("physical_level"),
        senior_tag=job.get("senior_tag"),
        age_min=job.get("age_min"),
        age_max=job.get("age_max"),
    )


def get_recommendations(params: JobRequestDTO) -> List[JobCard]:
    """
    지역 기반 1차 필터링 후 rank score 기준 top3 공고를 반환합니다.

    처리 순서:
        1. region + job_type + physical_limit으로 1차 필터링 (DB 쿼리)
        2. delta 가중치 원점수 계산
        3. 0~1 정규화 후 rank score 내림차순 정렬
        4. TOP_N 반환
    """
    raw_jobs = job_repository.search_jobs(
        {
            "region": params.region,
            "job_type": params.job_type,
            "physical_limit": params.physical_limit,
            "work_type": params.work_type,
            "salary_min": params.salary_min,
        }
    )

    if not raw_jobs:
        return []

    w = load_weights()
    max_score = calc_max_score(w)
    ranked = sorted(
        raw_jobs,
        key=lambda j: normalize(calc_raw_score(j, params, w), max_score),
        reverse=True,
    )
    return [_to_job_card(job) for job in ranked[:TOP_N]]
