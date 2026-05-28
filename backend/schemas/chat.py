from typing import Any, Dict, List

from pydantic import BaseModel, Field

from backend.schemas.job import JobCard


class ChatRequestDTO(BaseModel):
    user_id: int = Field(..., gt=0, description="유저 ID")
    message: str = Field(..., min_length=1, max_length=1000, description="사용자 메시지")


class ChatResponseDTO(BaseModel):
    user_id: int = Field(..., description="유저 ID")
    text: str = Field(..., description="LLM 대화 텍스트 (말풍선에 표시)")
    jobs: List[JobCard] = Field(
        default_factory=list, description="추천 공고 목록 (추천 시에만 채워짐, 그 외 빈 배열)"
    )


class RecommendMoreRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="유저 ID")
    exclude_job_ids: List[str] = Field(default_factory=list, description="제외할 공고 UUID 목록")


class ChatMessageDTO(BaseModel):
    id: int
    role: str = Field(..., description="'user' | 'assistant'")
    content: str
    jobs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str


class ChatHistoryDTO(BaseModel):
    user_id: int
    messages: List[ChatMessageDTO]
