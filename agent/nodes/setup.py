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
import logging
import time

import httpx
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm
from agent.memory import memory
from agent.nodes.intent import classify_intent
from agent.parsers import RobustPydanticParser
from agent.state import AgentState
from backend.config import config
from backend.models.schemas import IntentType, ProfileInfo

logger = logging.getLogger(__name__)

_parser = RobustPydanticParser(pydantic_object=ProfileInfo)

_extractor_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """사용자 메시지에서 일자리 관련 조건 정보를 추출하세요.

추출 대상:
- job_type       : 희망 직종 (예: "경비", "청소", "요양보호사")
- region         : 거주/희망 근무 지역 (예: "서울", "강남구", "수원", "경기도")
                   ※ 반드시 실제 지명(시·구·동·도)이어야 합니다.
                   ✘ null로 처리 → "집 근처", "가까운 곳", "멀리는 못 가", "집에서 가까운",
                                    "동네", "근처", "가까운데", "우리 동네"
                      (이런 표현은 거리 선호일 뿐, 지역이 아닙니다)
- physical_limit : 신체적 제약 여부
                   true  → "어렵지 않게", "가벼운 일만", "힘든 건 못해", "몸이 불편", "무릎이 안 좋아",
                            "어려운 일은 못해", "힘든 일은 못해", "가벼운 거만", "몸이 안 좋아"
                   false → "건강해", "몸 괜찮아", "힘든 것도 가능", "몸 멀쩡해"
                   ※ "어렵다"는 표현은 신체 제약(true)으로 해석하세요
- work_type      : 근무 형태 ("시간제"/"part_time" 또는 "전일제"/"full_time" 또는 "any")
                   "잠깐만", "몇 시간만" → part_time
                   "매일", "정규직" → full_time
- salary_min     : 최소 희망 급여 (숫자만, 단위 제거. 예: 150만원 → 1500000)
- experience     : 경력 내용

규칙:
- 이번 메시지에서 언급된 것만 추출하세요
- 간접적인 표현도 적극적으로 해석하세요
- 언급되지 않은 항목은 반드시 null로 설정하세요
- 추측하거나 지어내지 마세요 — 메시지에 없으면 null

예시:
  입력: "일자리 추천받고 싶어요"
  출력: {{"job_type": null, "region": null, "physical_limit": null, "work_type": null, "salary_min": null, "experience": null}}

  입력: "안녕하세요, 일 구하고 싶어요"
  출력: {{"job_type": null, "region": null, "physical_limit": null, "work_type": null, "salary_min": null, "experience": null}}

  입력: "서울 강남구에서 경비 일 구해요"
  출력: {{"job_type": "경비", "region": "강남구", "physical_limit": null, "work_type": null, "salary_min": null, "experience": null}}

{format_instructions}""",
            ),
            ("human", "사용자 메시지: {user_message}"),
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


async def _fetch_user_profile(user_id: str) -> dict:
    """GET /users/{user_id} API 호출로 유저 프로필 조회."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.API_BASE_URL}/users/{user_id}",
                timeout=5.0,
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning("유저 프로필 API 호출 실패 (user_id=%s): %s", user_id, e)
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
    # ① 프로필 추출  ② 의도 분류  ③ GET /users/{user_id} API 호출
    t0 = time.perf_counter()
    new_info, intent_result, db_profile = await asyncio.gather(
        _extract_profile(user_message),
        classify_intent(user_message, history_text),
        _fetch_user_profile(user_id),
    )
    print(f"[Setup] gather(추출+의도+프로필) ⏱ {time.perf_counter() - t0:.2f}s")
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
        # refresh_jobs는 무조건 JOB_RECOMMEND로 라우팅
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
