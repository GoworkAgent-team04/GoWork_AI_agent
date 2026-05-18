"""
JWT 인증 서비스

흐름:
  1. POST /auth/token  → user_id 전달 → JWT 발급
  2. 이후 모든 /chat 요청에 Authorization: Bearer <token> 헤더 포함
  3. verify_token() 이 토큰을 검증하고 user_id 반환
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import config

_security = HTTPBearer()


def create_token(user_id: str) -> str:
    """user_id를 담은 JWT 토큰을 생성합니다."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    """
    Authorization 헤더의 Bearer 토큰을 검증하고 user_id를 반환합니다.
    FastAPI Depends()로 사용합니다.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            config.SECRET_KEY,
            algorithms=["HS256"],
        )
        return payload["sub"]  # user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다. 다시 로그인해 주세요.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )
