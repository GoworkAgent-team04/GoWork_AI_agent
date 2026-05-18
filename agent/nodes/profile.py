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
            (
                "system",
                """사용자의 메시지를 아래 세 가지로 분류하세요.

READ    : 본인 프로필 정보 조회 요청
          예) "내 정보 보여줘", "내 프로필 확인"

UPDATE  : 특정 필드를 명시적으로 수정 요청
          예) "지역을 서울로 바꿔줘", "직종을 청소로 수정해줘"
          → field(DB 컬럼명)와 value도 추출
          수정 가능한 field: region_city, region_district, preferred_job_category,
                            preferred_work_type, physical_level, career_type, experience_desc

COLLECT : 대화 중 자연스럽게 개인 정보를 언급하는 경우
          예) "저는 서울 강남구에 살아요", "무릎이 좀 불편해서요",
              "시간제로만 일할 수 있어요", "예전에 경비 일 해봤어요"

{format_instructions}""",
            ),
            (
                "human",
                """[대화 기록]
{history}

[사용자 메시지]
{user_message}""",
            ),
        ]
    )
    | fast_llm
    | _action_classifier_parser
)

# ─── Response Generator ──────────────────────────────────────────────────────

_response_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 친절한 일자리 상담사입니다.
프로필 관련 처리 결과를 상황에 맞게 안내하세요.

READ    → 핵심 정보만 보기 좋게 정리해서 보여주세요
UPDATE  → 변경된 내용을 확인해주고 격려해주세요
COLLECT → 사용자가 언급한 정보를 자연스럽게 확인하는 한 문장만 말하세요.
          딱딱하게 "저장했습니다" 같은 말은 하지 말고, 대화 흐름에 녹여주세요.
          예) "강남구 쪽에서 일하실 수 있군요, 참고할게요 😊"
              "몸이 불편하신 부분이 있으시군요, 가벼운 업무 위주로 찾아드릴게요"
- 반드시 한국어로 답변하세요""",
            ),
            (
                "human",
                """[작업 유형]
{action_type}

[처리 결과]
{result}

[사용자 메시지]
{user_message}""",
            ),
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
