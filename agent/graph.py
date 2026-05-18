"""
LangGraph 메인 그래프

흐름:
  START
    └─ setup_node  (메모리 로드 · 프로필 추출 · 의도 분류 — 3개 동시 실행)
         ├─ JOB_RECOMMEND
         │    └─ profile_checker_node  (정보 충족 확인 · 검색 파라미터 추출 — 2개 동시 실행)
         │         ├─ 정보 부족 → question_gen_node → END
         │         └─ 정보 충분 → job_searcher_node
         │                          ├─ 결과 충분 (≥3건) → job_response_gen_node → END
         │                          └─ 결과 부족 → param_relaxer_node
         │                               ├─ retry < MAX → job_searcher_node (루프)
         │                               └─ retry ≥ MAX → job_response_gen_node → END
         ├─ JOB_INQUIRY  → job_inquiry_node  → END
         ├─ JOB_APPLY    → job_apply_node    → END
         ├─ PROFILE      → profile_handler_node → END
         └─ GENERAL_CHAT → general_chat_node → END
"""

import time

from langgraph.graph import END, StateGraph

from agent.nodes.general_chat import general_chat_node
from agent.nodes.job_apply import job_apply_node
from agent.nodes.job_inquiry import job_inquiry_node
from agent.nodes.job_recommend import (
    job_response_gen_node,
    job_searcher_node,
    param_relaxer_node,
    profile_checker_node,
    question_gen_node,
)
from agent.nodes.profile import profile_handler_node
from agent.nodes.setup import setup_node
from agent.state import AgentState
from backend.config import config
from backend.models.schemas import IntentType

# ─── 노드 실행 로거 ───────────────────────────────────────────────────────────

_BOLD = "\033[1m"
_RESET = "\033[0m"
_BLUE = "\033[34m"
_GREEN = "\033[32m"
_GRAY = "\033[90m"

# 노드명 → 한국어 설명
_NODE_DESC = {
    "setup": "프로필 추출 · 의도 분류 · DB 조회 (동시)",
    "profile_checker": "정보 충족 확인 · 파라미터 추출 (동시)",
    "question_gen": "추가 질문 생성",
    "job_searcher": "DB 일자리 검색",
    "param_relaxer": "검색 조건 완화",
    "job_response_gen": "일자리 추천 응답 생성",
    "job_inquiry": "공고 문의 처리",
    "job_apply": "지원 처리",
    "profile_handler": "프로필 조회/수정/저장",
    "general_chat": "일반 대화 응답 생성",
}


def _node(name: str, fn):
    """노드 함수를 감싸 실행 시작·완료·소요시간을 터미널에 출력합니다."""
    if not config.LOG_LLM:
        return fn

    desc = _NODE_DESC.get(name, "")

    async def wrapper(state):
        print(f"{_BLUE}{_BOLD}● {name}{_RESET}{_GRAY}  {desc}{_RESET}")
        t = time.time()
        result = await fn(state)
        elapsed = time.time() - t

        summary = _summarize(name, result)
        print(f"{_GREEN}  ✔ {elapsed:.2f}s{_RESET}{_GRAY}  {summary}{_RESET}")
        return result

    return wrapper


def _summarize(name: str, result: dict) -> str:
    """노드 결과에서 핵심 값만 뽑아 한 줄로 요약합니다."""
    if not result:
        return ""
    if name == "setup":
        info = result.get("extracted_info") or {}
        extracted = {k: v for k, v in info.items() if v is not None}
        intent = result.get("intent", "?")
        return f"intent={intent}  추출={extracted}" if extracted else f"intent={intent}"
    if name == "profile_checker":
        sufficient = result.get("is_info_sufficient")
        missing = result.get("missing_fields", [])
        return f"sufficient={sufficient}  missing={missing}"
    if name == "job_searcher":
        return f"검색결과 {len(result.get('jobs', []))}건"
    if name == "param_relaxer":
        return f"retry={result.get('retry_count', '?')}  params={result.get('search_params', {})}"
    if name in (
        "job_response_gen",
        "question_gen",
        "general_chat",
        "job_inquiry",
        "job_apply",
        "profile_handler",
    ):
        text = result.get("response", "")
        return f'"{text[:60]}…"' if len(text) > 60 else f'"{text}"'
    return ""


# 결과가 이 건수 이상이면 재검색 안 함
MIN_JOBS_THRESHOLD = 3
# 최대 파라미터 완화 재시도 횟수
MAX_RETRIES = 2


# ─── Conditional Edge 함수들 ──────────────────────────────────────────────────


def route_by_intent(state: AgentState) -> str:
    """Intent에 따라 각 파이프라인으로 라우팅"""
    intent = state.get("intent")
    if intent == IntentType.JOB_RECOMMEND:
        return "profile_checker"
    elif intent == IntentType.JOB_INQUIRY:
        return "job_inquiry"
    elif intent == IntentType.JOB_APPLY:
        return "job_apply"
    elif intent == IntentType.PROFILE:
        return "profile_handler"
    else:  # GENERAL_CHAT or fallback
        return "general_chat"


def route_after_profile_check(state: AgentState) -> str:
    """정보 충분 여부에 따라 질문 생성 또는 검색으로 분기"""
    return "job_searcher" if state.get("is_info_sufficient") else "question_gen"


def route_after_profile_handler(state: AgentState) -> str:
    """
    PROFILE 처리 후 라우팅.
    after_profile_intent가 JOB_RECOMMEND이면 일자리 추천 파이프라인으로 이어짐.
    """
    if state.get("after_profile_intent") == IntentType.JOB_RECOMMEND:
        return "profile_checker"
    return "__end__"


def route_after_job_search(state: AgentState) -> str:
    """검색 결과 수에 따라 응답 생성 또는 파라미터 완화로 분기"""
    jobs = state.get("jobs", [])
    retry_count = state.get("retry_count", 0)

    if len(jobs) >= MIN_JOBS_THRESHOLD or retry_count >= MAX_RETRIES:
        return "job_response_gen"
    else:
        return "param_relaxer"


# ─── 그래프 빌드 ──────────────────────────────────────────────────────────────


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # ── 노드 등록 ────────────────────────────────────────────────
    builder.add_node("setup", _node("setup", setup_node))
    builder.add_node("profile_checker", _node("profile_checker", profile_checker_node))
    builder.add_node("question_gen", _node("question_gen", question_gen_node))
    builder.add_node("job_searcher", _node("job_searcher", job_searcher_node))
    builder.add_node("param_relaxer", _node("param_relaxer", param_relaxer_node))
    builder.add_node("job_response_gen", _node("job_response_gen", job_response_gen_node))
    builder.add_node("job_inquiry", _node("job_inquiry", job_inquiry_node))
    builder.add_node("job_apply", _node("job_apply", job_apply_node))
    builder.add_node("profile_handler", _node("profile_handler", profile_handler_node))
    builder.add_node("general_chat", _node("general_chat", general_chat_node))

    # ── 진입점 ───────────────────────────────────────────────────
    builder.set_entry_point("setup")

    # setup → Intent에 따라 각 파이프라인으로 직접 라우팅
    builder.add_conditional_edges(
        "setup",
        route_by_intent,
        {
            "profile_checker": "profile_checker",
            "job_inquiry": "job_inquiry",
            "job_apply": "job_apply",
            "profile_handler": "profile_handler",
            "general_chat": "general_chat",
        },
    )

    # profile_checker → 질문 OR 검색 (param_extractor 단계 없음)
    builder.add_conditional_edges(
        "profile_checker",
        route_after_profile_check,
        {
            "question_gen": "question_gen",
            "job_searcher": "job_searcher",
        },
    )

    builder.add_edge("question_gen", END)

    # 검색 결과 → 응답 OR 파라미터 완화
    builder.add_conditional_edges(
        "job_searcher",
        route_after_job_search,
        {
            "job_response_gen": "job_response_gen",
            "param_relaxer": "param_relaxer",
        },
    )

    builder.add_edge("param_relaxer", "job_searcher")
    builder.add_edge("job_response_gen", END)
    builder.add_edge("job_inquiry", END)
    builder.add_edge("job_apply", END)
    builder.add_edge("general_chat", END)

    # profile_handler → after_profile_intent에 따라 분기
    builder.add_conditional_edges(
        "profile_handler",
        route_after_profile_handler,
        {
            "profile_checker": "profile_checker",
            "__end__": END,
        },
    )

    return builder.compile()


# 앱 전체에서 공유하는 컴파일된 그래프 (싱글톤)
graph = build_graph()
