"""
recommend_service 유닛 테스트

수정된 로직:
- _last_params_cache: 검색 파라미터 캐싱
- get_last_params: 캐시에서 파라미터 조회
- get_recommendations: exclude_ids 파라미터 지원
"""

from unittest.mock import patch

import pytest

from backend.schemas.job import JobRequestDTO
from backend.services import recommend_service


@pytest.fixture(autouse=True)
def clear_cache():
    """각 테스트 전후로 캐시 초기화"""
    recommend_service._last_params_cache.clear()
    yield
    recommend_service._last_params_cache.clear()


# ─── get_last_params ──────────────────────────────────────────────


def test_get_last_params_empty_cache():
    """캐시 없으면 None 반환"""
    result = recommend_service.get_last_params("1")
    assert result is None


def test_get_last_params_after_recommendation():
    """get_recommendations 호출 후 캐시에서 파라미터 조회"""
    params = JobRequestDTO(user_id=1, region="서울", job_type="경비")

    with patch("backend.services.recommend_service.job_repository.search_jobs", return_value=[]):
        recommend_service.get_recommendations(params)

    result = recommend_service.get_last_params("1")
    assert result is not None
    assert result.region == "서울"
    assert result.job_type == "경비"


def test_get_last_params_overwritten_by_new_search():
    """새 검색 시 캐시가 덮어써짐"""
    params1 = JobRequestDTO(user_id=1, region="서울")
    params2 = JobRequestDTO(user_id=1, region="부산")

    with patch("backend.services.recommend_service.job_repository.search_jobs", return_value=[]):
        recommend_service.get_recommendations(params1)
        recommend_service.get_recommendations(params2)

    result = recommend_service.get_last_params("1")
    assert result.region == "부산"


def test_get_last_params_different_users():
    """유저별로 캐시가 분리됨"""
    params1 = JobRequestDTO(user_id=1, region="서울")
    params2 = JobRequestDTO(user_id=2, region="부산")

    with patch("backend.services.recommend_service.job_repository.search_jobs", return_value=[]):
        recommend_service.get_recommendations(params1)
        recommend_service.get_recommendations(params2)

    assert recommend_service.get_last_params("1").region == "서울"
    assert recommend_service.get_last_params("2").region == "부산"


# ─── get_recommendations (exclude_ids) ───────────────────────────


def test_get_recommendations_empty_jobs():
    """검색 결과 없으면 빈 리스트"""
    params = JobRequestDTO(user_id=1, region="없는지역")
    with patch("backend.services.recommend_service.job_repository.search_jobs", return_value=[]):
        result = recommend_service.get_recommendations(params)
    assert result == []


def test_get_recommendations_exclude_ids():
    """exclude_ids에 포함된 공고는 결과에서 제외"""
    mock_jobs = [
        {
            "id": "aaa",
            "title_raw": "경비원",
            "source_url": "http://a.com",
            "location_city": "서울",
            "location_district": "노원구",
            "work_type_norm": None,
            "work_type_raw": "시간제",
            "salary_raw": "200만원",
            "salary_min": 2000000,
            "schedule_raw": None,
            "physical_level": "LOW",
            "senior_tag": "SENIOR_PREFERRED",
            "age_min": None,
            "age_max": None,
            "deadline_at": None,
            "deadline_type": "OPEN",
            "company_raw": "테스트",
            "embedding": None,
        },
        {
            "id": "bbb",
            "title_raw": "청소원",
            "source_url": "http://b.com",
            "location_city": "서울",
            "location_district": "노원구",
            "work_type_norm": None,
            "work_type_raw": "상시",
            "salary_raw": "180만원",
            "salary_min": 1800000,
            "schedule_raw": None,
            "physical_level": "MID",
            "senior_tag": None,
            "age_min": None,
            "age_max": None,
            "deadline_at": None,
            "deadline_type": "OPEN",
            "company_raw": "테스트2",
            "embedding": None,
        },
    ]

    params = JobRequestDTO(user_id=1, region="서울")
    with patch(
        "backend.services.recommend_service.job_repository.search_jobs", return_value=mock_jobs
    ):
        result = recommend_service.get_recommendations(params, exclude_ids=["aaa"])

    result_ids = [job.id for job in result]
    assert "aaa" not in result_ids
    assert "bbb" in result_ids


def test_get_recommendations_exclude_all():
    """전체 공고가 exclude_ids에 포함되면 빈 리스트"""
    mock_jobs = [
        {
            "id": "aaa",
            "title_raw": "경비원",
            "source_url": "http://a.com",
            "location_city": "서울",
            "location_district": None,
            "work_type_norm": None,
            "work_type_raw": None,
            "salary_raw": None,
            "salary_min": None,
            "schedule_raw": None,
            "physical_level": None,
            "senior_tag": None,
            "age_min": None,
            "age_max": None,
            "deadline_at": None,
            "deadline_type": "OPEN",
            "company_raw": None,
            "embedding": None,
        },
    ]

    params = JobRequestDTO(user_id=1, region="서울")
    with patch(
        "backend.services.recommend_service.job_repository.search_jobs", return_value=mock_jobs
    ):
        result = recommend_service.get_recommendations(params, exclude_ids=["aaa"])

    assert result == []
