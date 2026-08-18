from fastapi import APIRouter

from backend.repositories import job_repository
from backend.schemas.job import JobClickRequestDTO

router = APIRouter(tags=["JobClick"])


@router.post("/job-clicks", summary="지원하기 버튼 클릭 로그")
async def log_job_click(req: JobClickRequestDTO):
    """
    지원하기 버튼 클릭 이벤트를 저장합니다.
    """
    job_repository.save_job_click(
        user_id=req.user_id,
        job_id=req.job_id,
        event_type=req.event_type,
    )
    return {"status": "ok"}
