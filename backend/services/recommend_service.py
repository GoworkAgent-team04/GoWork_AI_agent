from typing import Any, Dict, List, Optional

import numpy as np

from backend.repositories import job_repository
from backend.schemas.job import JobCard, JobRequestDTO
from backend.scoring import calc_max_score, calc_raw_score, normalize
from backend.scoring.category import encode_text

TOP_N = 3


def _to_job_card(job: Dict[str, Any]) -> JobCard:
    """DB row → JobCard 변환"""
    location_parts = [job.get("location_city"), job.get("location_district")]
    location = " ".join(p for p in location_parts if p) or job.get("location_raw")

    deadline: Optional[str] = None
    if (job.get("deadline_type") or "").upper() == "OPEN":
        deadline = "상시모집"
    elif job.get("deadline_at"):
        deadline = str(job["deadline_at"])[:10]

    return JobCard(
        id=str(job["id"]),
        title=job.get("title_raw") or "",
        company=job.get("company_raw"),
        location=location,
        salary=job.get("salary_raw"),
        work_type=job.get("work_type_norm") or job.get("work_type_raw"),
        schedule=job.get("schedule_raw"),
        deadline=deadline,
        source_url=job.get("source_url"),
        physical_level=job.get("physical_level"),
        senior_tag=job.get("senior_tag"),
        age_min=job.get("age_min"),
        age_max=job.get("age_max"),
    )


def _batch_job_type_similarities(
    jobs: List[Dict[str, Any]], job_type: Optional[str]
) -> List[Optional[float]]:
    """전체 공고의 직종 유사도를 배치로 계산합니다.

    embedding이 저장된 공고는 DB 벡터를 사용하고,
    없는 공고는 None을 반환해 scorer에서 개별 계산하도록 fallback합니다.
    """
    if not job_type:
        return [None] * len(jobs)

    query_vec = encode_text(job_type)
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)

    has_emb_indices = [i for i, j in enumerate(jobs) if j.get("embedding")]
    sims: List[Optional[float]] = [None] * len(jobs)

    if has_emb_indices:
        vecs = np.array([jobs[i]["embedding"] for i in has_emb_indices], dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8
        batch_sims = (vecs / norms) @ query_norm
        for i, sim in zip(has_emb_indices, batch_sims):
            sims[i] = float(np.clip(sim, 0.0, 1.0))

    return sims


def get_recommendations(params: JobRequestDTO) -> List[JobCard]:
    """
    지역 기반 필터링 후 임베딩 배치 유사도 기준 top3 공고를 반환합니다.

    처리 순서:
        1. region + physical_limit으로 DB 필터링 (전체 조회, limit 없음)
        2. 직종 유사도 배치 계산 (저장된 임베딩 활용)
        3. 다중 가중치 원점수 계산 후 정규화
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

    max_score = calc_max_score()
    job_type_sims = _batch_job_type_similarities(raw_jobs, params.job_type)

    ranked = sorted(
        range(len(raw_jobs)),
        key=lambda i: normalize(
            calc_raw_score(raw_jobs[i], params, job_type_sim=job_type_sims[i]),
            max_score,
        ),
        reverse=True,
    )
    return [_to_job_card(raw_jobs[i]) for i in ranked[:TOP_N]]
