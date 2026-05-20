"""
job_apply_node

대화 기록에서 지원할 공고를 파악 → 중복 체크 후 DB에 지원 등록 → 결과 안내
"""

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm, main_llm
from agent.parsers import RobustPydanticParser
from agent.prompts import (
    APPLY_CONTEXT_HUMAN,
    APPLY_CONTEXT_SYSTEM,
    APPLY_RESPONSE_HUMAN,
    APPLY_RESPONSE_SYSTEM,
)
from agent.state import AgentState
from backend.database.queries import apply_to_job, get_job_detail
from backend.models.schemas import JobIdExtract

# ─── Context Resolver ────────────────────────────────────────────────────────

_context_resolver_parser = RobustPydanticParser(pydantic_object=JobIdExtract)

_context_resolver_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", APPLY_CONTEXT_SYSTEM),
            ("human", APPLY_CONTEXT_HUMAN),
        ]
    )
    | fast_llm
    | _context_resolver_parser
)

# ─── Response Generator ──────────────────────────────────────────────────────

_response_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", APPLY_RESPONSE_SYSTEM),
            ("human", APPLY_RESPONSE_HUMAN),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def job_apply_node(state: AgentState) -> dict:
    # Step 1: 어떤 공고에 지원하려는지 파악
    job_id_result = await _context_resolver_chain.ainvoke(
        {
            "last_jobs": state["last_jobs"],
            "history": state["history_text"],
            "user_message": state["user_message"],
            "format_instructions": _context_resolver_parser.get_format_instructions(),
        }
    )

    if not job_id_result.job_id:
        return {
            "response": (
                "어떤 일자리에 지원하시겠어요? 😊\n"
                "공고 이름이나 번호를 말씀해 주시면 바로 도와드릴게요!"
            )
        }

    # Step 2: 공고 상세 조회
    job_detail = await asyncio.to_thread(get_job_detail, job_id_result.job_id)

    if not job_detail:
        return {"response": "해당 일자리 정보를 찾을 수 없어요. 다시 한번 확인해 주시겠어요?"}

    # Step 3: DB 지원 처리
    result = await asyncio.to_thread(apply_to_job, state["user_id"], job_id_result.job_id)

    # Step 4: 결과 응답 생성
    response = await _response_chain.ainvoke(
        {
            "success": result.get("success", False),
            "duplicate": result.get("duplicate", False),
            "job_detail": job_detail,
            "user_message": state["user_message"],
        }
    )
    return {"response": response}
