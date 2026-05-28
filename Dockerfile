# ── 1단계: Python 의존성 설치 ────────────────────────────────────────
FROM python:3.11-slim AS python-builder

WORKDIR /app

RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
 && poetry install --without dev --no-root \
 && .venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu --force-reinstall

# ── 2단계: sentence-transformers 모델 사전 다운로드 ──────────────────
FROM python:3.11-slim AS model-downloader

WORKDIR /app
COPY --from=python-builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# ── 3단계: 최종 이미지 (소스코드 제외 - EC2 볼륨 마운트로 제공) ──────────
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 (psycopg2 등 런타임 의존성)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
 && rm -rf /var/lib/apt/lists/*

# Python 가상환경 복사
COPY --from=python-builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# sentence-transformers 캐시 복사 (cold start 방지)
COPY --from=model-downloader /root/.cache/huggingface /root/.cache/huggingface

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

# 소스코드는 EC2에서 볼륨 마운트로 제공
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
