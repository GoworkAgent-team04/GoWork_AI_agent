"""
setup_node

매 요청의 첫 번째 노드.
- 사용자 메시지를 메모리에 저장
- 아래 세 작업을 asyncio.gather로 동시 실행:
    ① 대화에서 조건 정보 추출 (fast_llm)
    ② 의도 분류 (fast_llm)  ← 기존 intent_classifier_node 통합
    ③ DB 사용자 프로필 조회
- 메모리 컨텍스트(대화 기록, 수집된 정보, 마지막 공고)를 state에 주입
"""

import asyncio

from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm
from agent.memory import memory
from agent.nodes.intent import classify_intent
from agent.parsers import RobustPydanticParser
from agent.prompts import EXTRACT_HUMAN, EXTRACT_SYSTEM
from agent.state import AgentState
from backend.database.queries import get_user_profile
from backend.models.schemas import IntentType, ProfileInfo

_parser = RobustPydanticParser(pydantic_object=ProfileInfo)

_extractor_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", EXTRACT_SYSTEM),
            ("human", EXTRACT_HUMAN),
        ]
    )
    | fast_llm
    | _parser
)


_REGION_VAGUE_SUFFIXES = ("쪽", "이요", "요", "에서", "근처", "동네")
_REGION_VAGUE_WORDS = {"집", "집근처", "근처", "동네", "우리동네", "가까운곳", "멀지않은곳"}


def _clean_region(region: str) -> str | None:
    """
    추출된 region을 정규화합니다.
    - 막연한 표현 → None
    - 불필요한 suffix 제거 ("성북구쪽" → "성북구", "서울이요" → "서울")
    """
    cleaned = region.strip()
    normalized = cleaned.replace(" ", "")

    if normalized in _REGION_VAGUE_WORDS:
        return None

    for suffix in _REGION_VAGUE_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
            break

    return cleaned or None


async def _extract_profile(user_message: str) -> dict:
    """메시지에서 조건 정보를 추출. 실패 시 빈 dict 반환."""
    try:
        result = await _extractor_chain.ainvoke(
            {
                "user_message": user_message,
                "format_instructions": _parser.get_format_instructions(),
            }
        )
        extracted = {k: v for k, v in result.model_dump().items() if v is not None}

        # region 정규화 (막연한 표현 제거, suffix 클리닝)
        if "region" in extracted:
            cleaned = _clean_region(str(extracted["region"]))
            if cleaned:
                extracted["region"] = cleaned
            else:
                del extracted["region"]

        return extracted
    except Exception:
        return {}


async def setup_node(state: AgentState) -> dict:
    user_id = state["user_id"]
    user_message = state["user_message"]

    # 사용자 메시지 메모리에 저장 (history 로드 전에 먼저 추가)
    memory.add_user_message(user_id, user_message)

    # 대화 기록 로드 (intent 분류에도 필요)
    history_text = memory.get_history_as_text(user_id)
    history_messages = memory.get_history(user_id)

    # ── 3개 작업 동시 실행 ────────────────────────────────────────
    # ① 프로필 추출  ② 의도 분류  ③ DB 프로필 조회
    new_info, intent_result, db_profile = await asyncio.gather(
        _extract_profile(user_message),
        classify_intent(user_message, history_text),
        asyncio.to_thread(get_user_profile, user_id),
    )
    db_profile = db_profile or {}

    # 추출된 조건 정보 누적 업데이트
    if new_info:
        memory.update_profile_info(user_id, new_info)

    collected_info = memory.get_profile_info(user_id)
    last_jobs = memory.get_last_jobs(user_id)

    # PROFILE_RECOMMEND → PROFILE 처리 후 JOB_RECOMMEND로 이어짐
    if intent_result.intent == IntentType.PROFILE_RECOMMEND:
        intent = IntentType.PROFILE
        after_profile_intent = IntentType.JOB_RECOMMEND
    else:
        intent = intent_result.intent
        after_profile_intent = None

    print(f"[Intent] {intent} (confidence: {intent_result.confidence:.2f})")

    # ── refresh_jobs 액션: 이전에 추천된 공고 ID를 제외 목록으로 세팅 ──
    action = state.get("action")
    if action == "refresh_jobs" and last_jobs:
        exclude_job_ids = [str(j["id"]) for j in last_jobs if j.get("id")]
        print(f"[Setup] refresh_jobs → 제외 공고 {len(exclude_job_ids)}건: {exclude_job_ids}")
        intent = IntentType.JOB_RECOMMEND
        after_profile_intent = None
    else:
        exclude_job_ids = []

    return {
        "history_text": history_text,
        "history_messages": history_messages,
        "collected_info": collected_info,
        "db_profile": db_profile,
        "last_jobs": last_jobs,
        "extracted_info": new_info,
        "intent": intent,
        "after_profile_intent": after_profile_intent,
        "retry_count": 0,
        "jobs": [],
        "exclude_job_ids": exclude_job_ids,
        "is_info_sufficient": None,
        "missing_fields": [],
        "search_params": None,
        "response": None,
    }
