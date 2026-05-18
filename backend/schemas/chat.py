from typing import List

from pydantic import BaseModel, Field

from backend.models.schemas import JobCard


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지", min_length=1)
    # user_id는 JWT 토큰에서 추출하므로 요청 바디에 포함하지 않음


class ChatResponse(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    text: str = Field(..., description="LLM 대화 텍스트 (말풍선에 표시)")
    jobs: List[JobCard] = Field(
        default_factory=list, description="공고 카드 목록 (일자리 추천 시에만 채워짐)"
    )
