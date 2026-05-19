from typing import Optional

from sqlalchemy import text

from backend.database.connection import get_db


def save_feedback(reviewer_id: int, job_id: str, rating: int, comment: Optional[str]) -> None:
    """feedbacks 테이블에 별점과 코멘트를 저장합니다."""
    with get_db() as db:
        db.execute(
            text(
                "INSERT INTO feedbacks (reviewer_id, job_id, rating, comment) "
                "VALUES (:reviewer_id, :job_id, :rating, :comment)"
            ),
            {"reviewer_id": reviewer_id, "job_id": job_id, "rating": rating, "comment": comment},
        )
        db.commit()
