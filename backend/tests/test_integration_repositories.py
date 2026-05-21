"""
Repository 통합 테스트 (실제 DB 연결)

users id 1~10: 스킬 없는 유저
users id 11~20: 스킬 있는 유저
"""

from backend.repositories import feedback_repository, job_repository, user_repository

# ─── User Repository ─────────────────────────────────────────────


def test_find_user_by_id_exists():
    """존재하는 유저 조회"""
    user = user_repository.find_user_by_id(1)
    assert user is not None
    assert user["id"] == 1
    assert "name" in user


def test_find_user_by_id_not_exists():
    """존재하지 않는 유저 → None"""
    user = user_repository.find_user_by_id(99999)
    assert user is None


def test_find_careers_no_skills_user():
    """스킬 없는 유저(1~10) 경력 → 빈 리스트"""
    careers = user_repository.find_careers_by_user_id(1)
    assert isinstance(careers, list)
    assert len(careers) == 0


def test_find_careers_with_skills_user():
    """스킬 있는 유저(11~20) 경력 → 데이터 존재"""
    careers = user_repository.find_careers_by_user_id(11)
    assert isinstance(careers, list)
    assert len(careers) > 0
    assert "company_name" in careers[0]
    assert "start_date" in careers[0]


def test_find_certifications_with_skills_user():
    """스킬 있는 유저 자격증 조회"""
    certs = user_repository.find_certifications_by_user_id(11)
    assert isinstance(certs, list)
    assert len(certs) > 0


def test_find_language_skills_with_skills_user():
    """스킬 있는 유저 어학 능력 조회"""
    skills = user_repository.find_language_skills_by_user_id(11)
    assert isinstance(skills, list)
    for skill in skills:
        assert "language" in skill
        assert "level" in skill


def test_find_document_skills_with_skills_user():
    """스킬 있는 유저 문서 툴 조회"""
    skills = user_repository.find_document_skills_by_user_id(11)
    assert isinstance(skills, list)


def test_find_other_skills_with_skills_user():
    """스킬 있는 유저 기타 역량 조회"""
    skills = user_repository.find_other_skills_by_user_id(11)
    assert isinstance(skills, list)


# ─── Job Repository ───────────────────────────────────────────────


def test_search_jobs_no_filter():
    """필터 없이 최신순 50건 조회"""
    jobs = job_repository.search_jobs({})
    assert isinstance(jobs, list)
    assert len(jobs) <= 50
    assert len(jobs) > 0


def test_search_jobs_with_region():
    """region 필터 적용"""
    jobs = job_repository.search_jobs({"region": "서울"})
    assert isinstance(jobs, list)
    for job in jobs:
        location = (
            (job.get("location_city") or "")
            + (job.get("location_district") or "")
            + (job.get("location_raw") or "")
        )
        assert "서울" in location


def test_search_jobs_with_physical_limit():
    """physical_limit=True → LOW/MID 또는 NULL만"""
    jobs = job_repository.search_jobs({"physical_limit": True})
    for job in jobs:
        if job.get("physical_level") is not None:
            assert job["physical_level"] in ("LOW", "MID")


def test_search_jobs_result_fields():
    """필수 필드 존재 확인"""
    jobs = job_repository.search_jobs({})
    assert len(jobs) > 0
    job = jobs[0]
    assert "id" in job
    assert "title_raw" in job
    assert "source_url" in job


def test_find_job_by_id_not_exists():
    """존재하지 않는 공고 → None"""
    job = job_repository.find_job_by_id("00000000-0000-0000-0000-000000000000")
    assert job is None


def test_find_job_source_url_not_exists():
    """존재하지 않는 공고 source_url → None"""
    url = job_repository.find_job_source_url("00000000-0000-0000-0000-000000000000")
    assert url is None


# ─── Feedback Repository ─────────────────────────────────────────


def test_save_feedback_with_comment():
    """feedback 저장 (comment 포함)"""
    feedback_repository.save_feedback(
        reviewer_id=1,
        job_id="test-job-id",
        rating=4,
        comment="테스트 코멘트",
    )


def test_save_feedback_without_comment():
    """feedback 저장 (comment 없음)"""
    feedback_repository.save_feedback(
        reviewer_id=1,
        job_id="test-job-id",
        rating=5,
        comment=None,
    )


def test_save_feedback_invalid_rating():
    """rating 범위 초과 시 DB 제약 위반"""
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        feedback_repository.save_feedback(
            reviewer_id=1,
            job_id="test-job-id",
            rating=10,
            comment=None,
        )
