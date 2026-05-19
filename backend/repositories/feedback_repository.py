from typing import Optional

from backend.database.connection import get_db
from backend.models.orm import Feedback


def save_feedback(reviewer_id: int, job_id: str, rating: int, comment: Optional[str]) -> None:
    """feedbacks 테이블에 별점과 코멘트를 저장합니다."""
    with get_db() as db:
        feedback = Feedback(
            reviewer_id=reviewer_id,
            job_id=job_id,
            rating=rating,
            comment=comment,
        )
        db.add(feedback)
        db.commit()
