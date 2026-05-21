"""
공고 적합도 점수 계산 모듈

흐름:
    1. 파라미터 있는 항목만: score += base_weight * similarity
    2. 파라미터 없는 항목: 스킵 (제재 없음)
    3. raw_score 합산 후 max_score(1.20 고정) 기준 0~1 정규화
"""

from typing import Any, Dict, Optional

from backend.schemas.job import JobRequestDTO
from backend.scoring.category import text_similarity
from backend.scoring.weights import Weights

_WORK_TYPE_MAP = {
    "part_time": "PART_TIME",
    "full_time": "FULL_TIME",
    "any": None,
}

_weights = Weights()


def calc_raw_score(
    job: Dict[str, Any], params: JobRequestDTO, w: Optional[Weights] = None
) -> float:
    """파라미터 있는 항목만 base_weight * similarity 합산으로 원점수를 계산합니다."""
    if w is None:
        w = _weights
    score = 0.0

    # 직종: 임베딩 코사인 유사도
    if params.job_type:
        job_text = job.get("job_category_norm") or job.get("title_raw") or ""
        if job_text:
            score += w.job_type * text_similarity(params.job_type, job_text)

    # 신체 강도
    if params.physical_limit is not None:
        physical = job.get("physical_level")
        if physical is not None:
            matched = (params.physical_limit is True and physical in ("LOW", "MID")) or (
                params.physical_limit is False
            )
            score += w.physical_level * (1.0 if matched else 0.0)

    # 근무 형태
    if params.work_type:
        job_work_type = job.get("work_type_norm")
        if job_work_type is not None:
            db_work_type = _WORK_TYPE_MAP.get(params.work_type.lower(), "UNKNOWN")
            matched = db_work_type is None or job_work_type == db_work_type
            score += w.work_type * (1.0 if matched else 0.0)

    # 최소 급여
    if params.salary_min is not None:
        job_salary_min = job.get("salary_min")
        if job_salary_min is not None:
            matched = job_salary_min >= params.salary_min
            score += w.salary_min * (1.0 if matched else 0.0)

    # 시니어 태그 (param 무관, 항상 평가)
    senior_tag = job.get("senior_tag")
    if senior_tag is not None:
        senior_tag_str = str(senior_tag)
        if senior_tag_str in ("SENIOR_ONLY", "SENIOR_PREFERRED"):
            sim = 1.0
        elif senior_tag_str == "ANY":
            sim = 0.5
        else:
            sim = 0.0
        score += w.senior_tag * sim

    return score


def calc_max_score(w: Optional[Weights] = None) -> float:
    """고정 최대 가능 원점수를 반환합니다."""
    if w is None:
        w = _weights
    return w.job_type + w.physical_level + w.work_type + w.salary_min + w.senior_tag


def normalize(raw_score: float, max_score: float) -> float:
    """원점수를 0~1 사이 rank score로 정규화합니다."""
    if max_score == 0:
        return 0.0
    return raw_score / max_score
