from fastapi import APIRouter

from backend.schemas.auth import TokenRequest, TokenResponse
from backend.services.auth import create_token

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/auth/token", response_model=TokenResponse)
async def issue_token(req: TokenRequest):
    """
    user_id를 받아 JWT 토큰을 발급합니다.
    앱 로그인 시 호출하세요.
    """
    token = create_token(req.user_id)
    return TokenResponse(access_token=token)
