from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ─── Intent ──────────────────────────────────────────────────────


class IntentType(str, Enum):
    JOB_RECOMMEND = "JOB_RECOMMEND"  # 일자리 추천 요청
    JOB_INQUIRY = "JOB_INQUIRY"  # 특정 공고 문의
    JOB_APPLY = "JOB_APPLY"  # 지원/신청 요청
    PROFILE = "PROFILE"  # 내 정보 조회/수정
    PROFILE_RECOMMEND = "PROFILE_RECOMMEND"  # 개인 정보 언급 + 일자리 추천 동시 요청
    GENERAL_CHAT = "GENERAL_CHAT"  # 일반 대화


class IntentResult(BaseModel):
    intent: IntentType = Field(description="분류된 의도")
    confidence: float = Field(ge=0.0, le=1.0, description="분류 확신도 (0~1)")


# ─── Job Recommend ───────────────────────────────────────────────


class WorkType(str, Enum):
    FULL_TIME = "full_time"  # 전일제
    PART_TIME = "part_time"  # 시간제
    ANY = "any"  # 무관


class JobSearchParams(BaseModel):
    """DB 쿼리에 사용할 검색 파라미터"""

    job_type: Optional[str] = Field(None, description="희망 직종 (예: 경비, 청소, 요양보호사)")
    region: Optional[str] = Field(None, description="거주 지역 또는 근무 가능 지역")
    physical_limit: Optional[bool] = Field(
        None, description="신체적 제약 여부 (True면 가벼운 업무 필터)"
    )
    work_type: Optional[WorkType] = Field(None, description="근무 형태")
    salary_min: Optional[int] = Field(None, description="최소 희망 급여 (원)")
    experience: Optional[str] = Field(None, description="보유 경력")


class ProfileInfo(BaseModel):
    """대화 중 수집되는 사용자 조건 정보"""

    job_type: Optional[str] = None
    region: Optional[str] = None
    physical_limit: Optional[bool] = None
    work_type: Optional[str] = None
    salary_min: Optional[int] = None
    experience: Optional[str] = None


class MissingInfo(BaseModel):
    """필수 정보 누락 여부 판단 결과"""

    is_sufficient: bool = Field(description="필수 정보가 모두 수집됐는지 여부")
    missing_fields: List[str] = Field(default_factory=list, description="누락된 필드 목록")


# ─── Profile ─────────────────────────────────────────────────────


class ActionType(str, Enum):
    READ = "READ"  # 명시적 조회
    UPDATE = "UPDATE"  # 명시적 수정
    COLLECT = "COLLECT"  # 대화 중 개인 정보 언급 → 자동 저장


class ProfileAction(BaseModel):
    """프로필 작업 분류 결과"""

    action: ActionType = Field(description="작업 유형 (READ/UPDATE/COLLECT)")
    field: Optional[str] = Field(None, description="수정할 필드명 (UPDATE 시)")
    value: Optional[str] = Field(None, description="수정할 값 (UPDATE 시)")


# ─── Job Card (프론트엔드 렌더링용 공고 카드) ──────────────────────


class JobCard(BaseModel):
    """DB에서 직접 포맷팅된 공고 카드 — LLM 생성 없음, 할루시네이션 없음"""

    id: str  # 공고 UUID (지원 요청 시 사용)
    title: str  # 공고 제목 (title_raw)
    company: Optional[str]  # 회사명 (null이면 프론트에서 "미기재" 표시)
    location: Optional[str]  # 근무지 (city+district 조합 또는 location_raw)
    salary: Optional[str]  # 급여 원문 (null이면 "급여 협의")
    work_type: Optional[str]  # 근무형태
    schedule: Optional[str]  # 근무일정
    deadline: Optional[str]  # 마감일 (YYYY-MM-DD 또는 "상시모집", null이면 미기재)
    source_url: Optional[str]  # 원본 공고 링크


# ─── Job Context ─────────────────────────────────────────────────


class JobIdExtract(BaseModel):
    """대화에서 특정 공고 ID 추출 결과"""

    job_id: Optional[str] = Field(None, description="특정된 공고 UUID, 없으면 null")
