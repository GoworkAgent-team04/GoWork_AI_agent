"""
intent_classifier_node

fast_llm(gpt-4o-mini)으로 사용자 의도를 5가지로 분류합니다.
JOB_RECOMMEND / JOB_INQUIRY / JOB_APPLY / PROFILE / GENERAL_CHAT
"""

from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm
from agent.parsers import RobustPydanticParser
from agent.prompts import INTENT_HUMAN, INTENT_SYSTEM
from backend.models.schemas import IntentResult, IntentType

_parser = RobustPydanticParser(pydantic_object=IntentResult)

_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", INTENT_SYSTEM),
            ("human", INTENT_HUMAN),
        ]
    )
    | fast_llm
    | _parser
)


async def classify_intent(user_message: str, history: str) -> IntentResult:
    """setup_node에서 직접 호출 가능한 독립 함수."""
    try:
        return await _chain.ainvoke(
            {
                "user_message": user_message,
                "history": history,
                "format_instructions": _parser.get_format_instructions(),
            }
        )
    except Exception:
        return IntentResult(intent=IntentType.GENERAL_CHAT, confidence=0.0)
