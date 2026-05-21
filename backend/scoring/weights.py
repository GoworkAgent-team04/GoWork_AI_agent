"""
가중치 정의 모듈

score = Σ (base_weight * similarity)  ← 파라미터 있는 항목만
"""

from dataclasses import dataclass


@dataclass
class Weights:
    job_type: float = 0.35
    physical_level: float = 0.25
    work_type: float = 0.20
    salary_min: float = 0.20
    senior_tag: float = 0.20
