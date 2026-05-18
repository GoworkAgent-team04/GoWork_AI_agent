"""
사용자별 대화 메모리 관리.

- Short-term : 최근 N턴 대화 메시지 (ConversationBufferWindowMemory 역할)
- Collected  : 현재 세션에서 수집된 사용자 조건 정보
- Last Jobs  : 가장 최근에 추천한 공고 목록 (JOB_INQUIRY / JOB_APPLY에서 참조)
"""

from typing import Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.config import config
from backend.models.schemas import ProfileInfo


class ConversationMemory:
    def __init__(self):
        # user_id → 메시지 리스트
        self._histories: Dict[str, List[BaseMessage]] = {}
        # user_id → 대화 중 수집된 조건
        self._profiles: Dict[str, ProfileInfo] = {}
        # user_id → 마지막 추천 공고 목록
        self._last_jobs: Dict[str, List[Dict]] = {}

    # ─── 대화 기록 ────────────────────────────────────────────────

    def get_history(self, user_id: str) -> List[BaseMessage]:
        return self._histories.setdefault(user_id, [])

    def add_user_message(self, user_id: str, message: str):
        self.get_history(user_id).append(HumanMessage(content=message))
        self._trim(user_id)

    def add_ai_message(self, user_id: str, message: str):
        self.get_history(user_id).append(AIMessage(content=message))
        self._trim(user_id)

    def _trim(self, user_id: str):
        """최근 MAX_HISTORY_TURNS 턴만 유지 (메시지 쌍 기준)"""
        max_msgs = config.MAX_HISTORY_TURNS * 2
        history = self._histories[user_id]
        if len(history) > max_msgs:
            self._histories[user_id] = history[-max_msgs:]

    def get_history_as_text(self, user_id: str) -> str:
        """프롬프트에 삽입할 텍스트 형식 대화 기록"""
        history = self.get_history(user_id)
        if not history:
            return "대화 기록 없음"
        lines = []
        for msg in history:
            role = "사용자" if isinstance(msg, HumanMessage) else "AI"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    # ─── 수집된 조건 정보 ─────────────────────────────────────────

    def get_profile_info(self, user_id: str) -> ProfileInfo:
        return self._profiles.setdefault(user_id, ProfileInfo())

    def update_profile_info(self, user_id: str, updates: dict):
        """대화에서 새로 알게 된 조건 정보를 누적 업데이트"""
        profile = self.get_profile_info(user_id)
        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

    # ─── 마지막 추천 공고 ─────────────────────────────────────────

    def set_last_jobs(self, user_id: str, jobs: List[dict]):
        self._last_jobs[user_id] = jobs

    def get_last_jobs(self, user_id: str) -> List[dict]:
        return self._last_jobs.get(user_id, [])

    # ─── 세션 초기화 ──────────────────────────────────────────────

    def clear(self, user_id: str):
        """사용자 세션 전체 초기화"""
        self._histories.pop(user_id, None)
        self._profiles.pop(user_id, None)
        self._last_jobs.pop(user_id, None)


# 싱글톤 인스턴스 (앱 전체에서 공유)
memory = ConversationMemory()
