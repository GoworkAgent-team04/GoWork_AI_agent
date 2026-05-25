from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRequestDTO(BaseModel):
    user_id: int = Field(..., gt=0, description="유저 ID")


class CareerInfo(BaseModel):
    company_name: str
    job_title: str
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


class LanguageSkillInfo(BaseModel):
    language: str
    level: str


class UserResponseDTO(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    address: Optional[str] = None
    careers: List[CareerInfo] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    language_skills: List[LanguageSkillInfo] = Field(default_factory=list)
    document_skills: List[str] = Field(default_factory=list)
    other_skills: List[str] = Field(default_factory=list)
