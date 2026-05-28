import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from agent.memory import memory
from agent.router import process_message
from backend.repositories import chat_repository
from backend.schemas.chat import (
    ChatHistoryDTO,
    ChatMessageDTO,
    ChatRequestDTO,
    ChatResponseDTO,
    RecommendMoreRequest,
)
from backend.services import recommend_service

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)


def _save_exchange(user_id: int, user_msg: str, ai_text: str, jobs: list) -> None:
    """대화 교환을 DB에 저장합니다 (BackgroundTask용)."""
    try:
        session_id = chat_repository.get_or_create_session(user_id)
        chat_repository.save_message(session_id, "user", user_msg)
        chat_repository.save_message(
            session_id,
            "assistant",
            ai_text,
            [j["id"] if isinstance(j, dict) else j.id for j in jobs] if jobs else None,
        )
        # 추천 결과가 있으면 검색 파라미터도 저장
        if jobs:
            params = recommend_service.get_last_params(str(user_id))
            if params:
                chat_repository.save_search_params(session_id, user_id, params.model_dump())
    except Exception:
        logger.exception("chat DB 저장 실패 (user_id=%s)", user_id)


@router.post("/chat", response_model=ChatResponseDTO, summary="채팅 메시지 전송")
async def chat(req: ChatRequestDTO, background_tasks: BackgroundTasks):
    """
    사용자 메시지를 전송하고 AI 에이전트의 응답을 받습니다.

    - 일상 대화 / 문의 / 지원 / 프로필: `jobs`는 빈 배열 반환
    - 일자리 추천: `text` (말풍선) + `jobs` (공고 카드 top3) 반환
    """
    try:
        result = await process_message(str(req.user_id), req.message)
        response = ChatResponseDTO(
            user_id=req.user_id,
            text=result["text"],
            jobs=result["jobs"],
        )
        background_tasks.add_task(
            _save_exchange, req.user_id, req.message, result["text"], result["jobs"]
        )
        return response
    except Exception as e:
        logger.exception("chat error: %s", e)
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")


@router.post("/chat/stream", summary="채팅 스트리밍")
async def chat_stream(req: ChatRequestDTO):
    """
    텍스트 응답을 스트리밍으로 받습니다. 공고 카드가 필요하면 /chat을 사용하세요.
    """

    async def generate():
        try:
            result = await process_message(str(req.user_id), req.message)
            text = result["text"]
            chunk_size = 10
            for i in range(0, len(text), chunk_size):
                yield text[i : i + chunk_size]
                await asyncio.sleep(0.02)
        except Exception as e:
            logger.exception("chat stream error: %s", e)
            yield "[오류] 서버 오류가 발생했습니다."

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/chat/history", response_model=ChatHistoryDTO, summary="대화 기록 조회")
async def get_history(user_id: int = Query(..., gt=0)):
    """
    사용자의 최근 대화 기록을 반환합니다.
    """
    try:
        messages = await asyncio.to_thread(chat_repository.get_recent_messages, user_id)
        return ChatHistoryDTO(
            user_id=user_id,
            messages=[ChatMessageDTO(**m) for m in messages],
        )
    except Exception as e:
        logger.exception("get_history error: %s", e)
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")


@router.post("/chat/recommend-more", response_model=ChatResponseDTO, summary="다른 공고 추천")
async def recommend_more(req: RecommendMoreRequest, background_tasks: BackgroundTasks):
    """
    이미 본 공고를 제외하고 다른 공고를 추천합니다.
    마지막 검색 조건을 재사용하므로 /chat으로 일자리 검색 후 사용하세요.
    """
    params = recommend_service.get_last_params(str(req.user_id))
    if not params:
        # 캐시 없으면 에이전트 프로필 메모리로 폴백
        from backend.schemas.job import JobRequestDTO

        profile = memory.get_profile_info(str(req.user_id))
        if profile and (profile.job_type or profile.region):
            params = JobRequestDTO(
                user_id=req.user_id,
                job_type=profile.job_type,
                region=profile.region,
                physical_limit=profile.physical_limit,
                work_type=profile.work_type,
                salary_min=profile.salary_min,
            )
        else:
            return ChatResponseDTO(
                user_id=req.user_id,
                text="먼저 일자리를 검색해주세요.",
                jobs=[],
            )

    try:
        jobs = await asyncio.to_thread(
            recommend_service.get_recommendations, params, req.exclude_job_ids
        )
    except Exception as e:
        logger.exception("recommend_more error: %s", e)
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

    text = "다른 공고 찾아봤어요!" if jobs else "조건에 맞는 다른 공고가 없어요."
    background_tasks.add_task(_save_exchange, req.user_id, "다른 공고 추천받기", text, jobs)
    return ChatResponseDTO(user_id=req.user_id, text=text, jobs=jobs)


@router.delete("/chat/history", summary="대화 기록 초기화")
async def clear_history(user_id: int = Query(..., gt=0)):
    """
    특정 사용자의 대화 기록을 초기화하고 새 세션을 시작합니다.
    """
    memory.clear(str(user_id))
    await asyncio.to_thread(chat_repository.create_session, user_id)
    return {"message": "대화 기록이 초기화되었습니다."}
