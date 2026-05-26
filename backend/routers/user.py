from fastapi import APIRouter, HTTPException, Path

from backend.schemas.user import UserResponseDTO
from backend.services import user_service

router = APIRouter(tags=["User"])


@router.get("/users/{user_id}", response_model=UserResponseDTO, summary="유저 정보 조회")
async def get_user(user_id: int = Path(..., gt=0)):
    """
    유저 ID로 프로필 전체를 조회합니다.

    - 경력, 자격증, 어학, 문서 툴, 기타 역량 포함
    - 앱 시작 시 LLM context 주입용으로 사용
    """
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user
