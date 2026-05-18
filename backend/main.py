"""
FastAPI 애플리케이션 생성 및 설정

실행:
  uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, chat

app = FastAPI(
    title="시니어 구인구직 AI 에이전트",
    version="1.0.0",
)

# ─── 미들웨어 ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실서비스 시 앱 도메인으로 제한
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 라우터 등록 ──────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
