"""
공고 적합도 점수 계산 모듈

흐름:
    1. load_weights()로 가중치 로드 (파일 기반, 학습 후 업데이트 가능)
    2. 각 항목 delta = base_weight * (match_coeff or mismatch_coeff)
    3. param / job 필드 null이면 해당 항목 0점 처리
    4. raw_score 합산 후 max_score 기준 0~1 정규화
"""

from typing import Any, Dict

from backend.schemas.job import JobRequestDTO
from backend.scoring.category import category_similarity, infer_category
from backend.scoring.weights import load_weights

_WORK_TYPE_MAP = {
    "part_time": "PART_TIME",
    "full_time": "FULL_TIME",
    "any": None,
}


def _delta(base: float, similarity: float, match_coeff: float, mismatch_coeff: float) -> float:
    """
    유사도(0~1)에 따라 delta를 반환합니다.
    similarity=1.0 → base * match_coeff
    similarity=0.0 → base * mismatch_coeff
    중간값은 선형 보간
    """
    coeff = mismatch_coeff + (match_coeff - mismatch_coeff) * similarity
    return base * coeff


def calc_raw_score(job: Dict[str, Any], params: JobRequestDTO, w=None) -> float:
    """파라미터 유무 기반 delta 합산으로 원점수를 계산합니다."""
    if w is None:
        w = load_weights()
    score = 0.0

    # 직종: job_category_norm 우선, null이면 title_raw로 추론
    if params.job_type:
        req_cat = infer_category(params.job_type)
        job_cat = job.get("job_category_norm") or infer_category(job.get("title_raw") or "")
        if req_cat and job_cat:
            sim = category_similarity(req_cat, job_cat)
            score += _delta(w.job_type, sim, w.match_coeff, w.mismatch_coeff)
        elif req_cat or job_cat:
            score += _delta(w.job_type, 0.0, w.match_coeff, w.mismatch_coeff)
        # 둘 다 null → 0

    # 신체 강도
    if params.physical_limit is not None:
        physical = job.get("physical_level")
        if physical is not None:
            matched = (params.physical_limit is True and physical in ("LOW", "MID")) or (
                params.physical_limit is False
            )
            score += _delta(
                w.physical_level, 1.0 if matched else 0.0, w.match_coeff, w.mismatch_coeff
            )

    # 근무 형태
    if params.work_type:
        job_work_type = job.get("work_type_norm")
        if job_work_type is not None:
            db_work_type = _WORK_TYPE_MAP.get(params.work_type.lower(), "UNKNOWN")
            matched = db_work_type is None or job_work_type == db_work_type
            score += _delta(w.work_type, 1.0 if matched else 0.0, w.match_coeff, w.mismatch_coeff)

    # 최소 급여
    if params.salary_min is not None:
        job_salary_min = job.get("salary_min")
        if job_salary_min is not None:
            matched = job_salary_min >= params.salary_min
            score += _delta(w.salary_min, 1.0 if matched else 0.0, w.match_coeff, w.mismatch_coeff)

    # 시니어 태그 (param 무관, 항상 평가)
    # SENIOR_ONLY / SENIOR_PREFERRED → 시니어 특화 (+)
    # ANY                            → 중립 (0.5)
    # MIDDLE_PREFERRED               → 시니어 비선호 (-)
    # null                           → 0
    senior_tag = job.get("senior_tag")
    if senior_tag is not None:
        senior_tag_str = str(senior_tag)
        if senior_tag_str in ("SENIOR_ONLY", "SENIOR_PREFERRED"):
            sim = 1.0
        elif senior_tag_str == "ANY":
            sim = 0.5
        else:
            sim = 0.0
        score += _delta(w.senior_tag, sim, w.match_coeff, w.mismatch_coeff)

    return score


def calc_max_score(params: JobRequestDTO, w=None) -> float:
    """파라미터 존재 여부에 따른 최대 가능 원점수를 반환합니다."""
    if w is None:
        w = load_weights()
    max_score = w.senior_tag  # 항상 평가
    if params.job_type:
        max_score += w.job_type
    if params.physical_limit is not None:
        max_score += w.physical_level
    if params.work_type:
        max_score += w.work_type
    if params.salary_min is not None:
        max_score += w.salary_min
    return max_score


def normalize(raw_score: float, max_score: float) -> float:
    """원점수를 0~1 사이 rank score로 정규화합니다."""
    if max_score == 0:
        return 0.0
    min_score = -max_score
    return (raw_score - min_score) / (max_score - min_score)
