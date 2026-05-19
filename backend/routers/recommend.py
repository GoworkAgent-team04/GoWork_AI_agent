from fastapi import APIRouter, HTTPException

from backend.schemas.job import JobRequestDTO, JobResponseDTO

router = APIRouter(tags=["Recommend"])


@router.post("/recommend", response_model=JobResponseDTO, summary="공고 추천")
async def recommend(req: JobRequestDTO):
    """
    LLM이 추출한 유저 선호도 파라미터 기반으로 공고를 추천합니다.

    처리 순서:
    1. user_id로 유저 정보 DB 조회
    2. 지역(region) 기반 1차 필터링
    3. 가중치 계산 (직종, 신체강도, 근무형태, 급여)
    4. top3 공고 반환
    """
    # TODO: 가중치 계산 및 추천 로직 구현
    raise HTTPException(status_code=501, detail="추천 로직 구현 예정")
