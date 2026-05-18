from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID (UUID)")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = "bearer"
