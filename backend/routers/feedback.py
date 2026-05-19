from fastapi import APIRouter

from backend.schemas.feedback import FeedbackRequestDTO, FeedbackResponseDTO
from backend.services import feedback_service

router = APIRouter(tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponseDTO, summary="공고 피드백 제출")
async def submit_feedback(req: FeedbackRequestDTO):
    """
    추천받은 공고에 대한 별점 및 피드백을 제출합니다.

    - `rating`: 1~5점
    - `comment`: 선택 입력
    - 추후 추천 가중치 개선에 활용됩니다.
    """
    feedback_service.submit_feedback(req)
    return FeedbackResponseDTO(message="피드백이 접수되었습니다.")
