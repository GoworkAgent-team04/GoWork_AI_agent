"""
직종 텍스트 유사도 모듈 (임베딩 기반)

sentence-transformers를 사용해 한국어 텍스트 간 코사인 유사도를 계산합니다.
모델은 최초 호출 시 1회 로드 후 메모리에 캐싱됩니다.
"""

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def text_similarity(text1: str, text2: str) -> float:
    """두 텍스트 간 코사인 유사도를 반환합니다 (0~1)."""
    model = _get_model()
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    cos_sim = float(
        np.dot(embeddings[0], embeddings[1])
        / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
    )
    return max(0.0, min(1.0, cos_sim))
