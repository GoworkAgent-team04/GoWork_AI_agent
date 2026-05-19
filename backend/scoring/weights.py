"""
가중치 관리 모듈

Base 가중치  : 각 항목의 기본 반영 비율
Delta 가중치 : 일치/불일치 시 base에 곱해지는 증감 계수

추후 피드백 데이터 기반으로 학습된 값을 load_weights()를 통해 주입 가능.
현재는 파일 기반 초기값 사용.
"""

import json
import os
from dataclasses import dataclass

_WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "weights.json")


@dataclass
class Weights:
    # Base 가중치 (항목별 반영 비율)
    job_type: float = 0.35
    physical_level: float = 0.25
    work_type: float = 0.20
    salary_min: float = 0.20
    senior_tag: float = 0.20

    # Delta 계수 (일치 시 base * match_coeff, 불일치 시 base * mismatch_coeff)
    match_coeff: float = 1.0
    mismatch_coeff: float = -1.0


def load_weights() -> Weights:
    """
    weights.json이 존재하면 파일에서 로드, 없으면 기본값 반환.
    학습 후 weights.json을 업데이트하면 자동으로 반영됨.
    """
    if not os.path.exists(_WEIGHTS_FILE):
        return Weights()

    with open(_WEIGHTS_FILE) as f:
        data = json.load(f)

    allowed = {f.name for f in Weights.__dataclass_fields__.values()}
    return Weights(**{k: v for k, v in data.items() if k in allowed})


def save_weights(weights: Weights) -> None:
    """학습된 가중치를 weights.json에 저장합니다."""
    with open(_WEIGHTS_FILE, "w") as f:
        json.dump(weights.__dict__, f, indent=2, ensure_ascii=False)
