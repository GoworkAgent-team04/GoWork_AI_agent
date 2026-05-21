"""
/chat 엔드포인트 테스트
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_chat_missing_fields():
    """필수 필드 없으면 422"""
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_invalid_user_id():
    """user_id=0 이면 422"""
    response = client.post("/chat", json={"user_id": 0, "message": "안녕"})
    assert response.status_code == 422


def test_chat_empty_message():
    """빈 메시지면 422"""
    response = client.post("/chat", json={"user_id": 1, "message": ""})
    assert response.status_code == 422


def test_chat_message_too_long():
    """메시지 1000자 초과 시 422"""
    response = client.post("/chat", json={"user_id": 1, "message": "a" * 1001})
    assert response.status_code == 422


def test_chat_response_structure():
    """정상 응답 구조 확인"""
    response = client.post("/chat", json={"user_id": 1, "message": "안녕하세요"})
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "text" in data
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_chat_history_delete_invalid_user_id():
    """user_id=0 이면 422"""
    response = client.delete("/chat/history?user_id=0")
    assert response.status_code == 422


def test_chat_history_delete():
    """대화 이력 초기화 정상 처리"""
    response = client.delete("/chat/history?user_id=1")
    assert response.status_code == 200
    assert response.json()["message"] == "대화 기록이 초기화되었습니다."
