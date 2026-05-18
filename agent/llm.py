from langchain_groq import ChatGroq

from agent.llm_logger import LLMLogger
from backend.config import config

_callbacks_main = [LLMLogger("MAIN LLM")] if config.LOG_LLM else []
_callbacks_fast = [LLMLogger("FAST LLM")] if config.LOG_LLM else []

# 사용자에게 보이는 최종 응답 생성용 (고품질)
main_llm = ChatGroq(
    model=config.MAIN_MODEL,
    api_key=config.GROQ_API_KEY,
    temperature=config.MAIN_TEMPERATURE,
    callbacks=_callbacks_main,
)

# 의도 분류 / 파라미터 추출 / 판단 작업용 (빠름)
fast_llm = ChatGroq(
    model=config.FAST_MODEL,
    api_key=config.GROQ_API_KEY,
    temperature=config.FAST_TEMPERATURE,
    callbacks=_callbacks_fast,
)
