from backend.repositories import feedback_repository
from backend.schemas.feedback import FeedbackRequestDTO


def submit_feedback(req: FeedbackRequestDTO) -> None:
    """별점과 코멘트를 분리해서 feedbacks 테이블에 저장합니다."""
    feedback_repository.save_feedback(
        reviewer_id=req.user_id,
        job_id=req.job_id,
        rating=req.rating,
        comment=req.comment,
    )
