"""
/users 엔드포인트 테스트
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_get_user_not_found():
    """존재하지 않는 유저 404"""
    response = client.get("/users/99999")
    assert response.status_code == 404


def test_get_user_response_structure():
    """정상 응답 구조 확인"""
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "careers" in data
    assert "certifications" in data
    assert "language_skills" in data
    assert "document_skills" in data
    assert "other_skills" in data


def test_get_user_with_skills():
    """스킬 있는 유저 (id: 11~20) 조회"""
    response = client.get("/users/11")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 11


def test_get_user_without_skills():
    """스킬 없는 유저 (id: 1~10) 조회"""
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert isinstance(data["careers"], list)
    assert isinstance(data["certifications"], list)
