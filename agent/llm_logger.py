"""
LLM 입출력 로거

모든 LLM 호출의 프롬프트와 응답을 터미널에 출력합니다.
개발/디버깅 전용 — 운영 환경에서는 config.LOG_LLM = False 로 비활성화하세요.

출력 예시:
  ┌─────────────────────────────────────────────
  │ [FAST LLM] intent_classifier  ·  0.31s
  ├─ 입력 ──────────────────────────────────────
  │  사용자의 메시지를 분류하세요...
  ├─ 출력 ──────────────────────────────────────
  │  {"intent": "JOB_RECOMMEND", "confidence": 0.95}
  └─────────────────────────────────────────────
"""

import time
from typing import Any, Dict, List, Union

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# 터미널 색상 코드
_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_GRAY = "\033[90m"
_RED = "\033[31m"


class LLMLogger(BaseCallbackHandler):
    """LLM 입출력을 터미널에 구조화해서 출력하는 콜백 핸들러"""

    def __init__(self, label: str):
        """
        Args:
            label: "MAIN LLM" 또는 "FAST LLM" — 로그에 표시될 이름
        """
        self.label = label
        self._start_time: float = 0.0

    # ─── 호출 시작 ────────────────────────────────────────────────
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        self._start_time = time.time()
        prompt_text = prompts[0] if prompts else ""

        print(f"\n{_CYAN}{'─' * 60}{_RESET}")
        print(f"{_BOLD}{_CYAN}▶ [{self.label}]{_RESET}")
        print(f"{_YELLOW}── 입력 {'─' * 50}{_RESET}")
        # 너무 길면 앞 1500자만 출력
        if len(prompt_text) > 1500:
            print(prompt_text[:1500])
            print(f"{_GRAY}... (이하 {len(prompt_text) - 1500}자 생략){_RESET}")
        else:
            print(prompt_text)

    # ─── 호출 완료 ────────────────────────────────────────────────
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        elapsed = time.time() - self._start_time
        output = ""
        if response.generations and response.generations[0]:
            output = response.generations[0][0].text

        print(f"{_GREEN}── 출력 ({elapsed:.2f}s) {'─' * 44}{_RESET}")
        if len(output) > 800:
            print(output[:800])
            print(f"{_GRAY}... (이하 {len(output) - 800}자 생략){_RESET}")
        else:
            print(output)
        print(f"{_CYAN}{'─' * 60}{_RESET}\n")

    # ─── 호출 오류 ────────────────────────────────────────────────
    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        **kwargs: Any,
    ) -> None:
        elapsed = time.time() - self._start_time
        print(f"{_RED}── 오류 ({elapsed:.2f}s): {error}{_RESET}")
        print(f"{_CYAN}{'─' * 60}{_RESET}\n")
