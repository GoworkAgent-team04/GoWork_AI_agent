"""
job_inquiry_node

대화 기록에서 어떤 공고에 대한 질문인지 파악 → 공고 상세 조회 → 응답 생성
"""

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm, main_llm
from agent.parsers import RobustPydanticParser
from agent.state import AgentState
from backend.database.queries import get_job_detail
from backend.models.schemas import JobIdExtract

# ─── Context Resolver ────────────────────────────────────────────────────────

_context_resolver_parser = RobustPydanticParser(pydantic_object=JobIdExtract)

_context_resolver_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """대화 기록과 최근 추천 공고 목록을 보고
사용자가 문의하려는 공고의 job_id를 파악하세요.

- "이 일", "첫번째꺼", "경비 일", "아까 보여줬던" 등 간접 표현도 추론하세요
- 특정할 수 없으면 job_id를 null로 반환하세요

{format_instructions}""",
            ),
            (
                "human",
                """[최근 추천 공고 목록]
{last_jobs}

[대화 기록]
{history}

[현재 사용자 메시지]
{user_message}""",
            ),
        ]
    )
    | fast_llm
    | _context_resolver_parser
)

# ─── Response Generator ──────────────────────────────────────────────────────

_response_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 친절한 일자리 상담사입니다.
공고 상세 정보를 이해하기 쉽게 설명해드립니다.

- 중요한 정보(근무지, 급여, 근무시간, 연락처)를 먼저 안내하세요
- 이해하기 쉬운 말투 사용
- 지원 방법도 함께 안내해주세요
- 반드시 한국어로 답변하세요""",
            ),
            (
                "human",
                """[공고 상세 정보]
{job_detail}

[사용자 메시지]
{user_message}""",
            ),
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
                "말씀하신 공고를 찾지 못했어요.\n"
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
