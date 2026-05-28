"""
chat_repository 통합 테스트 (실제 DB 연결)

테스트 대상:
- get_or_create_session
- save_message
- save_search_params  ← 신규 추가된 함수
- get_recent_messages
"""

import pytest

from backend.repositories import chat_repository


@pytest.fixture
def session_id():
    """테스트용 세션 생성 (user_id=1 사용)"""
    return chat_repository.get_or_create_session(1)


# ─── get_or_create_session ────────────────────────────────────────


def test_get_or_create_session_returns_int():
    """세션 ID가 정수로 반환됨"""
    sid = chat_repository.get_or_create_session(1)
    assert isinstance(sid, int)
    assert sid > 0


def test_get_or_create_session_same_user_same_session():
    """같은 유저는 같은 최신 세션 반환"""
    sid1 = chat_repository.get_or_create_session(1)
    sid2 = chat_repository.get_or_create_session(1)
    assert sid1 == sid2


def test_create_session_new():
    """새 세션 생성 시 이전과 다른 ID"""
    sid1 = chat_repository.get_or_create_session(1)
    sid2 = chat_repository.create_session(1)
    assert sid2 > sid1


# ─── save_message ─────────────────────────────────────────────────


def test_save_user_message(session_id):
    """유저 메시지 저장"""
    chat_repository.save_message(session_id, "user", "안녕하세요")


def test_save_assistant_message_with_jobs(session_id):
    """어시스턴트 메시지 + 공고 ID 배열 저장"""
    job_ids = ["e6733c64-2bd5-4bc0-82ac-93c103c2b3aa", "851cbdea-ee46-4db5-8f0f-9ea9d36cdeda"]
    chat_repository.save_message(session_id, "assistant", "공고를 찾았어요!", job_ids)


def test_save_assistant_message_no_jobs(session_id):
    """어시스턴트 메시지 (job_ids 없음) 저장"""
    chat_repository.save_message(session_id, "assistant", "안녕하세요!", None)


# ─── save_search_params ───────────────────────────────────────────


def test_save_search_params_full(session_id):
    """검색 파라미터 전체 저장"""
    params = {
        "region": "서울",
        "job_type": "경비",
        "work_type": "part_time",
        "physical_limit": True,
        "salary_min": 2000000,
    }
    chat_repository.save_search_params(session_id, 1, params)


def test_save_search_params_region_only(session_id):
    """region만 있는 경우 저장"""
    params = {"region": "대전"}
    chat_repository.save_search_params(session_id, 1, params)


def test_save_search_params_all_none(session_id):
    """모든 파라미터가 None인 경우 저장"""
    params = {
        "region": None,
        "job_type": None,
        "work_type": None,
        "physical_limit": None,
        "salary_min": None,
    }
    chat_repository.save_search_params(session_id, 1, params)


# ─── get_recent_messages ──────────────────────────────────────────


def test_get_recent_messages_returns_list():
    """메시지 목록이 리스트로 반환됨"""
    messages = chat_repository.get_recent_messages(1)
    assert isinstance(messages, list)


def test_get_recent_messages_fields():
    """각 메시지에 필수 필드 존재"""
    chat_repository.save_message(chat_repository.get_or_create_session(1), "user", "테스트")
    messages = chat_repository.get_recent_messages(1)
    assert len(messages) > 0
    msg = messages[0]
    assert "id" in msg
    assert "role" in msg
    assert "content" in msg
    assert "job_ids" in msg
    assert "created_at" in msg


def test_get_recent_messages_no_session():
    """세션 없는 유저 → 빈 리스트"""
    messages = chat_repository.get_recent_messages(99999)
    assert messages == []
