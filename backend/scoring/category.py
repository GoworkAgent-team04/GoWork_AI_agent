"""
직종 카테고리 추론 및 유사도 모듈
"""

from typing import Dict, Optional

# ─── 직종 키워드 → 카테고리 매핑 ──────────────────────────────────

_KEYWORD_TO_CATEGORY: Dict[str, str] = {
    "경비": "SECURITY",
    "보안": "SECURITY",
    "시설관리": "SECURITY",
    "청소": "CLEANING",
    "환경미화": "CLEANING",
    "요양": "CARE",
    "돌봄": "CARE",
    "케어": "CARE",
    "간병": "CARE",
    "요양보호사": "CARE",
    "주방": "KITCHEN",
    "조리": "KITCHEN",
    "요리": "KITCHEN",
    "식당": "KITCHEN",
    "운전": "DRIVING",
    "드라이버": "DRIVING",
    "기사": "DRIVING",
    "판매": "SALES",
    "영업": "SALES",
    "매장": "SALES",
    "사무": "OFFICE",
    "행정": "OFFICE",
    "총무": "OFFICE",
    "생산": "PRODUCTION",
    "제조": "PRODUCTION",
    "공장": "PRODUCTION",
    "배달": "DELIVERY",
    "배송": "DELIVERY",
    "택배": "DELIVERY",
    "상담": "COUNSELING",
    "환경": "ENVIRONMENT",
}

# ─── 카테고리 간 유사도 행렬 (단방향 정의, 조회 시 양방향 처리) ────

_CATEGORY_SIMILARITY: Dict[tuple, float] = {
    ("SECURITY", "CLEANING"): 0.6,
    ("SECURITY", "DRIVING"): 0.5,
    ("SECURITY", "ENVIRONMENT"): 0.4,
    ("CLEANING", "ENVIRONMENT"): 0.7,
    ("CARE", "COUNSELING"): 0.6,
    ("CARE", "KITCHEN"): 0.5,
    ("KITCHEN", "SALES"): 0.4,
    ("DRIVING", "DELIVERY"): 0.8,
    ("DRIVING", "SECURITY"): 0.5,
    ("DELIVERY", "SALES"): 0.4,
    ("SALES", "OFFICE"): 0.5,
    ("OFFICE", "COUNSELING"): 0.6,
    ("PRODUCTION", "ENVIRONMENT"): 0.5,
    ("PRODUCTION", "DELIVERY"): 0.4,
    ("COUNSELING", "CARE"): 0.6,
}


def infer_category(text: str) -> Optional[str]:
    """키워드 매칭으로 직종 카테고리를 추론합니다."""
    for keyword, category in _KEYWORD_TO_CATEGORY.items():
        if keyword in text:
            return category
    return None


def category_similarity(cat1: str, cat2: str) -> float:
    """두 카테고리 간 유사도를 반환합니다 (0~1). 동일 카테고리는 1.0."""
    if cat1 == cat2:
        return 1.0
    return _CATEGORY_SIMILARITY.get((cat1, cat2)) or _CATEGORY_SIMILARITY.get((cat2, cat1)) or 0.0
