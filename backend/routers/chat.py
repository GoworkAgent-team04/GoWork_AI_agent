import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agent.memory import memory
from agent.router import process_message
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.auth import verify_token

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: str = Depends(verify_token),
):
    """
    채팅 엔드포인트. Authorization: Bearer <token> 헤더 필요.

    응답:
      text - LLM 대화 텍스트 (말풍선에 표시)jobs - 공고 카드 목록 (일자리 추천 시에만 채워짐, 그 외에는 [])
    """
    try:
        result = await process_message(user_id, req.message)
        return ChatResponse(
            user_id=user_id,
            text=result["text"],
            jobs=result["jobs"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    user_id: str = Depends(verify_token),
):
    """
    스트리밍 채팅. Authorization: Bearer <token> 헤더 필요.
    text 부분만 스트리밍합니다. jobs 카드가 필요하면 /chat을 사용하세요.
    """

    async def generate():
        try:
            result = await process_message(user_id, req.message)
            text = result["text"]
            chunk_size = 10
            for i in range(0, len(text), chunk_size):
                yield text[i : i + chunk_size]
                await asyncio.sleep(0.02)
        except Exception as e:
            yield f"[오류] {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.delete("/chat/history")
async def clear_history(user_id: str = Depends(verify_token)):
    """내 대화 기록 초기화. Authorization: Bearer <token> 헤더 필요."""
    memory.clear(user_id)
    return {"message": "대화 기록이 초기화되었습니다."}
