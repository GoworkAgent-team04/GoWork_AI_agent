"""
LangGraph 공유 상태 정의

각 노드는 AgentState를 받아 업데이트할 필드만 dict로 반환합니다.
LangGraph는 반환된 dict를 기존 state에 merge합니다.
"""

from typing import Any, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # ─── 입력 ─────────────────────────────────────────────────────
    user_id: str
    user_message: str

    # ─── 메모리 컨텍스트 (setup_node에서 로드) ──────────────────────
    history_text: str
    history_messages: List[BaseMessage]
    collected_info: Any  # ProfileInfo (TypedDict는 Any로 허용)
    db_profile: dict
    last_jobs: List[dict]

    # ─── 이번 메시지에서 새로 추출된 프로필 정보 ──────────────────────
    extracted_info: dict  # setup_node에서 추출, profile_handler_node에서 DB 저장

    # ─── Intent 분류 결과 ─────────────────────────────────────────
    intent: Optional[str]  # IntentType 문자열 값
    after_profile_intent: Optional[str]  # PROFILE 처리 후 이어서 실행할 intent (예: JOB_RECOMMEND)

    # ─── Profile Check 결과 ───────────────────────────────────────
    is_info_sufficient: Optional[bool]
    missing_fields: List[str]

    # ─── 일자리 검색 관련 ─────────────────────────────────────────
    search_params: Optional[dict]  # 추출된 검색 파라미터
    retry_count: int  # DB 재검색 횟수
    jobs: List[dict]  # 검색된 공고 목록

    # ─── 최종 출력 ────────────────────────────────────────────────
    response: Optional[str]
