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


def encode_text(text: str) -> np.ndarray:
    """텍스트를 임베딩 벡터로 인코딩합니다."""
    return _get_model().encode([text], convert_to_numpy=True)[0]


def text_similarity(text1: str, text2: str, vec1: Optional[np.ndarray] = None) -> float:
    """두 텍스트 간 코사인 유사도를 반환합니다 (0~1).

    vec1이 주어지면 text1 인코딩을 생략하고 재사용합니다.
    """
    model = _get_model()
    if vec1 is None:
        embeddings = model.encode([text1, text2], convert_to_numpy=True)
        v1, v2 = embeddings[0], embeddings[1]
    else:
        v1 = vec1
        v2 = model.encode([text2], convert_to_numpy=True)[0]
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0.0:
        return 0.0
    cos_sim = float(np.dot(v1, v2) / norm)
    return max(0.0, min(1.0, cos_sim))
