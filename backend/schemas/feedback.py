from typing import Optional

from pydantic import BaseModel, Field


class FeedbackRequestDTO(BaseModel):
    user_id: int = Field(..., gt=0, description="유저 ID")
    job_id: str = Field(..., min_length=1, description="공고 UUID")
    rating: int = Field(..., ge=1, le=5, description="별점 (1~5)")
    comment: Optional[str] = Field(None, max_length=1000, description="피드백 코멘트 (선택)")


class FeedbackResponseDTO(BaseModel):
    message: str = Field(..., description="구체적인 피드백 내용")
