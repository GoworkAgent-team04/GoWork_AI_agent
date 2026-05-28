"""
job_inquiry_node

대화 기록에서 어떤 공고에 대한 질문인지 파악 → 공고 상세 조회 → 응답 생성
"""

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm, main_llm
from agent.parsers import RobustPydanticParser
from agent.prompts import (
    INQUIRY_CONTEXT_HUMAN,
    INQUIRY_CONTEXT_SYSTEM,
    INQUIRY_RESPONSE_HUMAN,
    INQUIRY_RESPONSE_SYSTEM,
)
from agent.state import AgentState
from backend.database.queries import get_job_detail
from backend.models.schemas import JobIdExtract

# ─── Context Resolver ────────────────────────────────────────────────────────

_context_resolver_parser = RobustPydanticParser(pydantic_object=JobIdExtract)

_context_resolver_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", INQUIRY_CONTEXT_SYSTEM),
            ("human", INQUIRY_CONTEXT_HUMAN),
        ]
    )
    | fast_llm
    | _context_resolver_parser
)

# ─── Response Generator ──────────────────────────────────────────────────────

_response_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", INQUIRY_RESPONSE_SYSTEM),
            ("human", INQUIRY_RESPONSE_HUMAN),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def job_inquiry_node(state: AgentState) -> dict:
    # Step 1: 어떤 공고인지 파악
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
                "어떤 일자리에 대해 궁금하신가요? 😊\n"
                "공고 번호나 이름을 말씀해 주시면 자세히 안내해 드릴게요!"
            )
        }

    # Step 2: 공고 상세 조회
    job_detail = await asyncio.to_thread(get_job_detail, job_id_result.job_id)

    if not job_detail:
        return {"response": "해당 일자리 정보를 찾을 수 없어요. 다시 한번 확인해 주시겠어요?"}

    # Step 3: 응답 생성
    response = await _response_chain.ainvoke(
        {
            "job_detail": job_detail,
            "user_message": state["user_message"],
        }
    )
    return {"response": response}
