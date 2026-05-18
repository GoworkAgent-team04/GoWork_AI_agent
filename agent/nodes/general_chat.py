"""
general_chat_node

일반 대화를 처리합니다. GPT-4o가 직접 응답합니다.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.llm import main_llm
from agent.state import AgentState

_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 따뜻하고 친절한 AI 일자리 상담사입니다.

대화 방식:
- 쉽고 친근한 말투를 사용하세요
- 공감을 먼저 표현하고 도움을 제공하세요
- 대화 중 자연스럽게 일자리 관련 주제로 이어갈 수 있으면 권유하세요
  예) "심심하다고 하셨는데, 가벼운 일자리를 찾아드릴까요?"
- 너무 길게 쓰지 말고 간결하게 답변하세요
- 반드시 한국어로 답변하세요""",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}"),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def general_chat_node(state: AgentState) -> dict:
    response = await _chain.ainvoke(
        {
            "user_message": state["user_message"],
            "history": state["history_messages"],
        }
    )
    return {"response": response}
