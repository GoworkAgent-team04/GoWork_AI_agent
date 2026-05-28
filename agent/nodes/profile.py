"""
profile_handler_node

세 가지 케이스를 처리합니다.

  READ    : "내 정보 보여줘" → DB 조회 → 결과 안내
  UPDATE  : "지역 바꿔줘"   → DB 수정 → 변경 확인
  COLLECT : "저 서울 살아요", "무릎이 불편해요" 등 대화 중 개인 정보 언급
            → setup_node에서 추출된 extracted_info를 DB에 자동 저장
            → 사용자가 의식하지 못하게 자연스럽게 응답
"""

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm, main_llm
from agent.parsers import RobustPydanticParser
from agent.prompts import (
    PROFILE_ACTION_HUMAN,
    PROFILE_ACTION_SYSTEM,
    PROFILE_RESPONSE_HUMAN,
    PROFILE_RESPONSE_SYSTEM,
)
from agent.state import AgentState
from backend.database.queries import _map_job_category, get_user_profile, update_user_profile
from backend.models.schemas import ActionType, ProfileAction

# ─── ProfileInfo 필드 → DB 컬럼 매핑 ─────────────────────────────────────────
# extracted_info 키(ProfileInfo 필드명) → DB users 테이블 컬럼명
_FIELD_TO_DB: dict = {
    "job_type": "preferred_job_category",
    "work_type": "preferred_work_type",
    "experience": "experience_desc",
}

# physical_limit(bool) → physical_level(enum)
_PHYSICAL_LEVEL_MAP = {True: "LOW", False: "HIGH"}


def _map_extracted_to_db(extracted_info: dict) -> list[tuple[str, str]]:
    """
    extracted_info(ProfileInfo 필드)를 DB 컬럼명-값 쌍의 리스트로 변환합니다.
    저장 가능한 필드만 반환합니다.
    """
    updates = []

    for field, value in extracted_info.items():
        if value is None:
            continue

        if field == "region":
            # 지역명 길이로 시/구 구분 (2글자 이하 → city, 초과 → district)
            col = "region_city" if len(str(value)) <= 2 else "region_district"
            updates.append((col, str(value)))

        elif field == "physical_limit":
            level = _PHYSICAL_LEVEL_MAP.get(value)
            if level:
                updates.append(("physical_level", level))

        elif field == "job_type":
            # 한글 직종명 → DB enum 변환
            category = _map_job_category(str(value))
            if category:
                updates.append(("preferred_job_category", category))

        elif field in _FIELD_TO_DB:
            updates.append((_FIELD_TO_DB[field], str(value)))

    return updates


# ─── Action Classifier ───────────────────────────────────────────────────────

_action_classifier_parser = RobustPydanticParser(pydantic_object=ProfileAction)

_action_classifier_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", PROFILE_ACTION_SYSTEM),
            ("human", PROFILE_ACTION_HUMAN),
        ]
    )
    | fast_llm
    | _action_classifier_parser
)

# ─── Response Generator ──────────────────────────────────────────────────────

_response_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", PROFILE_RESPONSE_SYSTEM),
            ("human", PROFILE_RESPONSE_HUMAN),
        ]
    )
    | main_llm
    | StrOutputParser()
)


# ─── Node ────────────────────────────────────────────────────────────────────


async def profile_handler_node(state: AgentState) -> dict:
    user_id = state["user_id"]
    user_message = state["user_message"]
    extracted_info = state.get("extracted_info", {})

    # Step 1: READ / UPDATE / COLLECT 분류
    action = await _action_classifier_chain.ainvoke(
        {
            "user_message": user_message,
            "history": state["history_text"],
            "format_instructions": _action_classifier_parser.get_format_instructions(),
        }
    )

    result = None

    # Step 2: 작업 실행
    if action.action == ActionType.READ:
        result = await asyncio.to_thread(get_user_profile, user_id)

    elif action.action == ActionType.UPDATE:
        if not action.field or not action.value:
            return {
                "response": "어떤 정보를 어떻게 바꾸고 싶으신가요? 구체적으로 말씀해 주세요. 😊"
            }
        success = await asyncio.to_thread(update_user_profile, user_id, action.field, action.value)
        result = {"success": success, "field": action.field, "value": action.value}

    elif action.action == ActionType.COLLECT:
        # extracted_info를 DB 컬럼으로 변환 후 저장
        db_updates = _map_extracted_to_db(extracted_info)
        saved = []
        for col, val in db_updates:
            ok = await asyncio.to_thread(update_user_profile, user_id, col, val)
            if ok:
                saved.append(col)
        print(f"[Profile COLLECT] 저장된 필드: {saved}")
        result = {"saved_fields": saved, "extracted": extracted_info}

    # Step 3: 응답 생성
    response = await _response_chain.ainvoke(
        {
            "action_type": action.action,
            "result": result,
            "user_message": user_message,
        }
    )
    return {"response": response}
