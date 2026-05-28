"""
general_chat_node

일반 대화를 처리합니다. GPT-4o가 직접 응답합니다.
"""

import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.llm import main_llm
from agent.prompts import GENERAL_CHAT_SYSTEM
from agent.state import AgentState

_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", GENERAL_CHAT_SYSTEM),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}"),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def general_chat_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    response = await _chain.ainvoke(
        {
            "user_message": state["user_message"],
            "history": state["history_messages"],
        }
    )
    print(f"[GeneralChat] main_llm ⏱ {time.perf_counter() - t0:.2f}s")
    return {"response": response}
