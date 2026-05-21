"""
/recommend 엔드포인트 테스트
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_recommend_missing_user_id():
    """user_id 없으면 422"""
    response = client.get("/recommend")
    assert response.status_code == 422


def test_recommend_invalid_user_id_zero():
    """user_id=0 이면 422"""
    response = client.get("/recommend?user_id=0")
    assert response.status_code == 422


def test_recommend_invalid_salary_min():
    """salary_min 음수면 422"""
    response = client.get("/recommend?user_id=1&salary_min=-1")
    assert response.status_code == 422


def test_recommend_response_structure():
    """정상 응답 구조 확인"""
    response = client.get("/recommend?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_recommend_jobs_max_top3():
    """최대 3개 반환"""
    response = client.get("/recommend?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) <= 3


def test_recommend_job_card_fields():
    """JobCard 필드 확인"""
    response = client.get("/recommend?user_id=1")
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    if jobs:
        job = jobs[0]
        assert "id" in job
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "salary" in job


def test_recommend_with_region():
    """region 파라미터 정상 처리"""
    response = client.get("/recommend?user_id=1&region=서울")
    assert response.status_code == 200


def test_recommend_with_job_type():
    """job_type 파라미터 정상 처리"""
    response = client.get("/recommend?user_id=1&job_type=경비")
    assert response.status_code == 200


def test_recommend_with_physical_limit_true():
    """physical_limit=true 정상 처리"""
    response = client.get("/recommend?user_id=1&physical_limit=true")
    assert response.status_code == 200


def test_recommend_with_physical_limit_false():
    """physical_limit=false 정상 처리"""
    response = client.get("/recommend?user_id=1&physical_limit=false")
    assert response.status_code == 200


def test_recommend_with_work_type():
    """work_type 파라미터 정상 처리"""
    response = client.get("/recommend?user_id=1&work_type=part_time")
    assert response.status_code == 200


def test_recommend_with_all_params():
    """모든 파라미터 정상 처리"""
    response = client.get(
        "/recommend?user_id=1&region=서울&job_type=경비&physical_limit=false&work_type=part_time&salary_min=1500000"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert len(data["jobs"]) <= 3


def test_recommend_process_time_header():
    """X-Process-Time-Ms 헤더 존재 확인"""
    response = client.get("/recommend?user_id=1")
    assert "x-process-time-ms" in response.headers
