import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from agent.memory import memory
from agent.router import process_message
from backend.schemas.chat import ChatRequestDTO, ChatResponseDTO

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponseDTO, summary="채팅 메시지 전송")
async def chat(req: ChatRequestDTO):
    """
    사용자 메시지를 전송하고 AI 에이전트의 응답을 받습니다.

    - 일상 대화 / 문의 / 지원 / 프로필: `jobs`는 빈 배열 반환
    - 일자리 추천: `text` (말풍선) + `jobs` (공고 카드 top3) 반환
    """
    try:
        result = await process_message(str(req.user_id), req.message)
        return ChatResponseDTO(
            user_id=req.user_id,
            text=result["text"],
            jobs=result["jobs"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            yield f"[오류] {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.delete("/chat/history", summary="대화 기록 초기화")
async def clear_history(user_id: int = Query(..., gt=0)):
    """
    특정 사용자의 대화 기록을 초기화합니다.
    """
    # Todo: softDelete 해야 함
    memory.clear(str(user_id))
    return {"message": "대화 기록이 초기화되었습니다."}
