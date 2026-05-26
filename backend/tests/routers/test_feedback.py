"""
/feedback 엔드포인트 테스트
"""


def test_feedback_missing_fields(client):
    """필수 필드 없으면 422"""
    response = client.post("/feedback", json={})
    assert response.status_code == 422


def test_feedback_invalid_user_id(client):
    """user_id=0 이면 422"""
    response = client.post(
        "/feedback",
        json={"user_id": 0, "job_id": "some-uuid", "rating": 3},
    )
    assert response.status_code == 422


def test_feedback_rating_too_low(client):
    """rating=0 이면 422"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "some-uuid", "rating": 0},
    )
    assert response.status_code == 422


def test_feedback_rating_too_high(client):
    """rating=6 이면 422"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "some-uuid", "rating": 6},
    )
    assert response.status_code == 422


def test_feedback_empty_job_id(client):
    """job_id 빈 문자열이면 422"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "", "rating": 3},
    )
    assert response.status_code == 422


def test_feedback_comment_too_long(client):
    """comment 1000자 초과 시 422"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "some-uuid", "rating": 3, "comment": "a" * 1001},
    )
    assert response.status_code == 422


def test_feedback_without_comment(client):
    """comment 없이 정상 저장"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "some-uuid", "rating": 5},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "피드백이 접수되었습니다."


def test_feedback_with_comment(client):
    """comment 포함 정상 저장"""
    response = client.post(
        "/feedback",
        json={"user_id": 1, "job_id": "some-uuid", "rating": 4, "comment": "좋은 공고였습니다."},
    )
    assert response.status_code == 200
