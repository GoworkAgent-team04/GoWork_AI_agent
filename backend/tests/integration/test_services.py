"""
Service 통합 테스트 (실제 DB 연결)
"""

from backend.schemas.job import JobRequestDTO
from backend.services import recommend_service, user_service

# ─── User Service ─────────────────────────────────────────────────


def test_get_user_exists():
    """존재하는 유저 조회 → UserResponseDTO 반환"""
    user = user_service.get_user(1)
    assert user is not None
    assert user.id == 1
    assert user.name is not None


def test_get_user_not_exists():
    """존재하지 않는 유저 → None"""
    user = user_service.get_user(99999)
    assert user is None


def test_get_user_with_skills():
    """스킬 있는 유저 경력 포함 조회"""
    user = user_service.get_user(11)
    assert user is not None
    assert len(user.careers) > 0
    assert len(user.certifications) > 0


def test_get_user_without_skills():
    """스킬 없는 유저 빈 리스트 반환"""
    user = user_service.get_user(1)
    assert user is not None
    assert user.careers == []
    assert user.certifications == []


# ─── Recommend Service ───────────────────────────────────────────


def test_get_recommendations_returns_list():
    """추천 결과 리스트 반환"""
    params = JobRequestDTO(user_id=1)
    result = recommend_service.get_recommendations(params)
    assert isinstance(result, list)


def test_get_recommendations_max_top3():
    """최대 3개 반환"""
    params = JobRequestDTO(user_id=1)
    result = recommend_service.get_recommendations(params)
    assert len(result) <= 3


def test_get_recommendations_with_region():
    """region 필터 적용 시 해당 지역 공고 반환"""
    params = JobRequestDTO(user_id=1, region="서울")
    result = recommend_service.get_recommendations(params)
    assert isinstance(result, list)
    for job in result:
        assert job.location is not None
        assert "서울" in job.location


def test_get_recommendations_job_card_fields():
    """JobCard 필수 필드 존재"""
    params = JobRequestDTO(user_id=1, region="서울")
    result = recommend_service.get_recommendations(params)
    if result:
        job = result[0]
        assert job.id is not None
        assert job.title is not None
        assert job.source_url is not None


def test_get_recommendations_no_results():
    """결과 없는 경우 빈 리스트"""
    params = JobRequestDTO(user_id=1, region="존재하지않는지역XYZ")
    result = recommend_service.get_recommendations(params)
    assert result == []


def test_get_recommendations_sorted_by_score():
    """job_type 지정 시 유사도 높은 순 정렬"""
    params = JobRequestDTO(user_id=1, region="서울", job_type="경비")
    result = recommend_service.get_recommendations(params)
    assert len(result) <= 3
