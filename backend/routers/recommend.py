from typing import Optional

from fastapi import APIRouter

from backend.schemas.job import JobRequestDTO, JobResponseDTO
from backend.services import recommend_service

router = APIRouter(tags=["Recommend"])


@router.get("/recommend", response_model=JobResponseDTO, summary="공고 추천")
async def recommend(
    user_id: int,
    region: Optional[str] = None,
    job_type: Optional[str] = None,
    physical_limit: Optional[bool] = None,
    work_type: Optional[str] = None,
    salary_min: Optional[int] = None,
):
    """
    LLM이 추출한 유저 선호도 파라미터 기반으로 공고를 추천합니다.

    처리 순서:
    1. region 기반 1차 필터링
    2. delta 가중치 점수 계산 후 0~1 정규화
    3. rank score 기준 top3 반환
    """
    req = JobRequestDTO(
        user_id=user_id,
        region=region,
        job_type=job_type,
        physical_limit=physical_limit,
        work_type=work_type,
        salary_min=salary_min,
    )
    jobs = recommend_service.get_recommendations(req)
    return JobResponseDTO(user_id=user_id, jobs=jobs)
