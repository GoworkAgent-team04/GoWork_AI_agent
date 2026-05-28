"""
메인 라우터

LangGraph graph를 invoke하여 사용자 메시지를 처리합니다.

그래프 내부 흐름:
  setup → intent_classifier → [pipeline 선택]
  (각 파이프라인은 agent/graph.py 참조)

메모리 저장은 setup_node(시작)와 router(응답 후)에서 처리합니다.
"""

import time
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.graph import graph
from agent.llm import main_llm
from agent.memory import memory
from backend.models.schemas import IntentType

_LAST_RESORT = "잠시 후 다시 말씀해 주세요. 😊"

_fallback_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 따뜻하고 친절한 일자리 상담사입니다.

지금 시스템 내부에서 예상치 못한 문제가 발생했습니다.
사용자에게 오류가 생겼다고 직접 말하지 마세요.
대화 흐름과 사용자 메시지를 보고 자연스럽게 응답하세요.
필요하다면 다시 의도를 파악하는 질문을 해도 좋습니다.
반드시 한국어로 답변하세요.""",
            ),
            (
                "human",
                """[대화 기록]
{history}

[사용자 메시지]
{user_message}""",
            ),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def _fallback_response(user_id: str, user_message: str) -> str:
    """에러 발생 시 main_llm이 대화 맥락을 보고 자연스럽게 응답."""
    try:
        return await _fallback_chain.ainvoke(
            {
                "history": memory.get_history_as_text(user_id),
                "user_message": user_message,
            }
        )
    except Exception:
        return _LAST_RESORT


_W = "\033[97m"  # 밝은 흰색
_M = "\033[35m"  # 마젠타
_G = "\033[32m"  # 초록
_DIM = "\033[2m"  # 흐림
_R = "\033[0m"  # 리셋
_B = "\033[1m"  # 굵게

_cycle_count = 0  # 전체 대화 사이클 카운터


async def process_message(user_id: str, user_message: str, action: str | None = None) -> Dict[str, Any]:
    """
    사용자 메시지를 처리하고 최종 응답을 반환합니다.

    Args:
        user_id     : 사용자 식별자 (UUID 문자열)
        user_message: 사용자가 입력한 텍스트

    Returns:
        {
            "text": str         - LLM 대화 텍스트 (말풍선에 표시)
            "jobs": List[dict]  - 공고 카드 목록 (JOB_RECOMMEND 시에만 채워짐)
        }
    """
    global _cycle_count
    _cycle_count += 1
    _start = time.time()

    # ── 사이클 시작 구분선 ────────────────────────────────────────
    print(f"\n{_M}{'━' * 64}{_R}")
    print(f"{_B}{_M}  # {_cycle_count}  사용자 ({user_id[:8]}…){_R}")
    print(f"{_W}{_B}  ❯ {user_message}{_R}")
    print(f"{_M}{'━' * 64}{_R}\n")

    try:
        # LangGraph 실행: 초기 state에 user_id, user_message, action 주입
        final_state = await graph.ainvoke(
            {
                "user_id": user_id,
                "user_message": user_message,
                "action": action,
            }
        )

        text = final_state.get("response") or _LAST_RESORT
        intent = final_state.get("intent")
        jobs = final_state.get("jobs", [])

        # JOB_RECOMMEND 결과 → 메모리에 공고 목록 저장 (문의·지원 노드에서 참조)
        if intent == IntentType.JOB_RECOMMEND and jobs:
            memory.set_last_jobs(user_id, jobs)

        # 대화 텍스트만 메모리에 저장 (카드 데이터는 저장 불필요)
        memory.add_ai_message(user_id, text)

        # JOB_RECOMMEND가 아니면 jobs는 항상 빈 배열
        if intent != IntentType.JOB_RECOMMEND:
            jobs = []

    except Exception as e:
        print(f"[Error] Graph 실행 중 오류: {e}")
        text = await _fallback_response(user_id, user_message)
        jobs = []

    # ── 사이클 종료 구분선 ────────────────────────────────────────
    elapsed = time.time() - _start
    job_count = len(jobs)
    print(f"\n{_G}{'─' * 64}{_R}")
    print(f"{_G}{_B}  ◀ 응답  {_DIM}({elapsed:.2f}s  공고 {job_count}건){_R}")
    print(f"{_W}  {text[:120]}{'…' if len(text) > 120 else ''}{_R}")
    print(f"{_G}{'─' * 64}{_R}\n")

    return {"text": text, "jobs": jobs}
