"""
scoring 모듈 유닛 테스트
"""

import pytest

from backend.scoring.category import text_similarity
from backend.scoring.scorer import calc_max_score, calc_raw_score, normalize
from backend.scoring.weights import Weights


def test_text_similarity_same():
    """동일 텍스트 유사도는 1.0에 가까워야 함"""
    sim = text_similarity("경비", "경비")
    assert sim > 0.99


def test_text_similarity_related():
    """관련 직종 유사도는 중간 이상"""
    sim = text_similarity("경비", "시설관리")
    assert sim > 0.5


def test_text_similarity_unrelated():
    """무관한 텍스트 유사도는 낮아야 함"""
    sim = text_similarity("경비", "요리사")
    assert sim < 0.7


def test_text_similarity_range():
    """유사도는 0~1 사이"""
    sim = text_similarity("청소", "환경미화")
    assert 0.0 <= sim <= 1.0


def test_calc_max_score_default():
    """기본 가중치 합산 1.20"""
    w = Weights()
    assert calc_max_score(w) == pytest.approx(1.20)


def test_normalize_max():
    """최대 점수 정규화 → 1.0"""
    assert normalize(1.20, 1.20) == pytest.approx(1.0)


def test_normalize_zero():
    """0점 정규화 → 0.0"""
    assert normalize(0.0, 1.20) == pytest.approx(0.0)


def test_normalize_max_zero():
    """max_score=0 이면 0.0 반환"""
    assert normalize(0.5, 0.0) == 0.0


def test_calc_raw_score_no_params(mock_job):
    """파라미터 없으면 senior_tag만 반영"""
    from backend.schemas.job import JobRequestDTO

    params = JobRequestDTO(user_id=1)
    score = calc_raw_score(mock_job, params)
    assert score == pytest.approx(Weights().senior_tag * 1.0)


def test_calc_raw_score_with_job_type(mock_job):
    """job_type 있으면 점수 증가"""
    from backend.schemas.job import JobRequestDTO

    params_with = JobRequestDTO(user_id=1, job_type="경비")
    params_without = JobRequestDTO(user_id=1)
    assert calc_raw_score(mock_job, params_with) >= calc_raw_score(mock_job, params_without)


@pytest.fixture
def mock_job():
    return {
        "title_raw": "아파트 경비원 모집",
        "job_category_norm": None,
        "work_type_norm": "PART_TIME",
        "salary_min": 2000000,
        "physical_level": "LOW",
        "senior_tag": "SENIOR_PREFERRED",
    }
