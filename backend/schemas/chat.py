from typing import List

from pydantic import BaseModel, Field

from backend.schemas.job import JobCard


class ChatRequestDTO(BaseModel):
    user_id: int = Field(..., description="유저 ID")
    message: str = Field(..., description="사용자 메시지", min_length=1)


class ChatResponseDTO(BaseModel):
    user_id: int = Field(..., description="유저 ID")
    text: str = Field(..., description="LLM 대화 텍스트 (말풍선에 표시)")
    jobs: List[JobCard] = Field(
        default_factory=list, description="추천 공고 목록 (추천 시에만 채워짐, 그 외 빈 배열)"
    )
