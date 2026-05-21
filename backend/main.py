"""
FastAPI 애플리케이션 생성 및 설정

실행:
  uvicorn backend.main:app --reload

Flutter 웹 빌드:
  cd frontend && flutter build web --release
  → frontend/build/web/ 생성 후 FastAPI가 정적 파일 서빙
"""

import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import chat, feedback, recommend, user

_FLUTTER_WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "build", "web")

app = FastAPI(
    title="GoWork AI Agent API",
    version="1.0.0",
    description="""
## 시니어 구인구직 AI 에이전트 API

### 응답 구조
- `text` : 말풍선에 표시할 LLM 응답 텍스트
- `jobs` : 일자리 추천 시 공고 카드 목록 (top3), 그 외 빈 배열 `[]`

### 렌더링 분기
- `jobs.length === 0` → 말풍선(text)만 렌더링
- `jobs.length > 0` → 말풍선(text) + 공고 카드 렌더링
""",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── 응답 시간 미들웨어 ───────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


# ─── 미들웨어 ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실서비스 시 앱 도메인으로 제한
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 라우터 등록 ──────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(recommend.router)
app.include_router(feedback.router)

# ─── Flutter 웹 정적 파일 서빙 ────────────────────────────────────
# API 라우터 등록 후 마지막에 마운트 (API 경로가 우선)
# flutter build web 실행 전에는 비활성화됨
if os.path.isdir(_FLUTTER_WEB_DIR):
    app.mount("/", StaticFiles(directory=_FLUTTER_WEB_DIR, html=True), name="frontend")
