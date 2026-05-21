from typing import Optional

from fastapi import APIRouter, Query

from backend.schemas.job import JobRequestDTO, JobResponseDTO
from backend.services import recommend_service

router = APIRouter(tags=["Recommend"])


@router.get("/recommend", response_model=JobResponseDTO, summary="공고 추천")
async def recommend(
    user_id: int = Query(..., gt=0),
    region: Optional[str] = None,
    job_type: Optional[str] = None,
    physical_limit: Optional[bool] = None,
    work_type: Optional[str] = None,
    salary_min: Optional[int] = Query(None, ge=0),
):
    """
    LLM이 추출한 유저 선호도 파라미터 기반으로 공고를 추천합니다.

    처리 순서:
    1. region / physical_limit 기반 1차 Hard Filtering
    2. 파라미터 있는 항목만 score += base_weight * similarity 계산
       - job_type: 임베딩 코사인 유사도
       - physical_level / work_type / salary_min: rule-based
       - senior_tag: 항상 평가
    3. score / max_score(1.20) 정규화 후 rank score 기준 top3 반환
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
