from typing import List, Optional

from pydantic import BaseModel, Field


class JobRequestDTO(BaseModel):
    user_id: int = Field(..., description="유저 ID")
    job_type: Optional[str] = Field(None, description="희망 직종 (예: 경비, 청소)")
    region: Optional[str] = Field(None, description="희망 근무 지역 (예: 강남구, 서울)")
    physical_limit: Optional[bool] = Field(None, description="신체 제약 여부")
    work_type: Optional[str] = Field(None, description="근무 형태 (part_time | full_time | any)")
    salary_min: Optional[int] = Field(None, ge=0, description="최소 희망 급여 (원, 예: 1500000)")


class JobCard(BaseModel):
    id: str = Field(..., description="공고 UUID")
    title: str = Field(..., description="공고 제목")
    company: Optional[str] = Field(None, description="회사명")
    location: Optional[str] = Field(None, description="근무지 (예: 서울 강남구)")
    salary: Optional[str] = Field(None, description="급여 원문")
    work_type: Optional[str] = Field(None, description="근무형태 (전일제/시간제)")
    schedule: Optional[str] = Field(None, description="근무 일정")
    deadline: Optional[str] = Field(None, description="마감일 (YYYY-MM-DD | 상시모집)")
    source_url: Optional[str] = Field(None, description="원본 공고 링크")
    physical_level: Optional[str] = Field(None, description="신체 강도 (LOW/MID/HIGH)")
    senior_tag: Optional[bool] = Field(None, description="시니어 특화 공고 여부")
    age_min: Optional[int] = Field(None, description="최소 나이 제한")
    age_max: Optional[int] = Field(None, description="최대 나이 제한")


class JobResponseDTO(BaseModel):
    user_id: int = Field(..., description="유저 ID")
    jobs: List[JobCard] = Field(default_factory=list, description="추천 공고 top3")
