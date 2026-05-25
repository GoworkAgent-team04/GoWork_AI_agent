"""
JOB_RECOMMEND 관련 노드 모음

노드 실행 순서:
  profile_checker_node  (코드 기반 region 확인 → LLM 1회 param 추출)
    └─ 정보 부족 → question_gen_node → END
    └─ 정보 충분 → job_searcher_node
                      └─ 결과 충분 → job_response_gen_node → END
                      └─ 결과 부족 → param_relaxer_node
                                        └─ 재시도 가능 → job_searcher_node (루프)
                                        └─ 최대 재시도 → job_response_gen_node → END
"""

import logging

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm, main_llm
from agent.nodes.setup import _clean_region
from agent.parsers import RobustPydanticParser
from agent.state import AgentState
from backend.config import config
from backend.models.schemas import JobSearchParams

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Profile Checker Node
# ─────────────────────────────────────────────────────────────────────────────


def _check_region_sufficient(collected_info: dict, db_profile: dict) -> tuple[bool, list]:
    """
    region + job_type 충족 여부를 코드로 판단 (LLM 불필요).
    - region: collected_info 또는 db_profile에 지역이 있고 막연한 표현이 아니면 OK
    - job_type: collected_info에 직종이 있으면 OK
    둘 다 있어야 True
    """
    missing = []

    region = (collected_info or {}).get("region")
    if not region or not _clean_region(str(region)):
        missing.append("region")

    job_type = (collected_info or {}).get("job_type")
    if not job_type:
        missing.append("job_type")

    return (len(missing) == 0), missing


async def profile_checker_node(state: AgentState) -> dict:
    collected = (
        state["collected_info"].model_dump()
        if hasattr(state["collected_info"], "model_dump")
        else state["collected_info"]
    )

    # ── 코드 기반 region 충족 여부 판단 (LLM 없음 → 신뢰성 보장) ──
    is_sufficient, missing_fields = _check_region_sufficient(collected, state["db_profile"])
    print(
        f"[ProfileChecker] sufficient={is_sufficient}  missing={missing_fields}  region={collected.get('region')}"
    )

    if not is_sufficient:
        return {
            "is_info_sufficient": False,
            "missing_fields": missing_fields,
            "search_params": None,
        }

    # ── 정보 충분 → 검색 파라미터 추출 (LLM 1회) ─────────────────
    try:
        params = await _param_extractor_chain.ainvoke(
            {
                "db_profile": str(state["db_profile"]),
                "collected_info": collected,
                "history": state["history_text"],
                "format_instructions": _param_extractor_parser.get_format_instructions(),
            }
        )
        search_params = params.model_dump(exclude_none=True)
    except Exception as e:
        print(f"[ProfileChecker] param 추출 오류, 기본 region만 사용: {e}")
        region = collected.get("region")
        search_params = {"region": region} if region else {}

    return {
        "is_info_sufficient": True,
        "missing_fields": [],
        "search_params": search_params,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Question Generator Node  (정보 부족 시)
# ─────────────────────────────────────────────────────────────────────────────

_question_gen_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 따뜻하고 친절한 일자리 상담사입니다.
부족한 정보를 자연스럽고 공손하게 질문합니다.

규칙:
- 반드시 한 번에 하나의 질문만 하세요
- 쉽고 간단한 표현을 사용하세요
- 딱딱하지 않고 대화하듯 물어보세요
- 반드시 한국어로 답변하세요""",
            ),
            (
                "human",
                """[부족한 정보 항목]
{missing_fields}

[대화 기록]
{history}

가장 중요한 정보 하나만 자연스럽게 질문해주세요.""",
            ),
        ]
    )
    | fast_llm
    | StrOutputParser()
)


async def question_gen_node(state: AgentState) -> dict:
    question = await _question_gen_chain.ainvoke(
        {
            "missing_fields": state["missing_fields"],
            "history": state["history_text"],
        }
    )
    return {"response": question}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Param Extractor (profile_checker_node 내부에서 동시 실행 — 독립 노드 없음)
# ─────────────────────────────────────────────────────────────────────────────

_param_extractor_parser = RobustPydanticParser(pydantic_object=JobSearchParams)

_param_extractor_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """대화 내용에서 일자리 검색 파라미터를 추출합니다.

규칙:
- region: 반드시 [대화에서 수집된 정보]의 region 값만 사용하세요.
  DB 프로필의 address(거주지 주소)는 절대 region으로 사용하지 마세요.
  사용자가 명시적으로 언급한 지역이 없으면 null로 설정하세요.
- 나머지 파라미터(job_type, physical_limit, work_type, salary_min)는
  DB 프로필과 대화에서 수집된 정보를 모두 활용하세요.
- 확신할 수 없는 값은 null로 설정하세요.

{format_instructions}""",
            ),
            (
                "human",
                """[DB 사용자 프로필]
{db_profile}

[대화에서 수집된 정보]
{collected_info}

[대화 기록]
{history}""",
            ),
        ]
    )
    | fast_llm
    | _param_extractor_parser
)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Job Searcher Node
# ─────────────────────────────────────────────────────────────────────────────


async def job_searcher_node(state: AgentState) -> dict:
    """GET /recommend API를 호출해 스코어링된 공고 top3를 조회합니다."""
    params = state.get("search_params") or {}
    retry_count = state.get("retry_count", 0)
    user_id = state["user_id"]

    # job_category_list는 /recommend API 미지원 → 제외
    api_params = {k: v for k, v in params.items() if v is not None and k != "job_category_list"}
    api_params["user_id"] = user_id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.API_BASE_URL}/recommend",
                params=api_params,
                timeout=10.0,
            )
            if resp.status_code == 200:
                jobs = resp.json().get("jobs", [])
            else:
                logger.warning("/recommend API 오류: status=%s", resp.status_code)
                jobs = []
    except Exception as e:
        logger.exception("/recommend API 호출 실패: %s", e)
        jobs = []

    print(f"[JobSearch] retry={retry_count}, params={api_params}, found={len(jobs)}건")
    return {"jobs": jobs}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Param Relaxer Node
# ─────────────────────────────────────────────────────────────────────────────
# 재검색 전략
# ┌─ retry_count == 0 (1차 완화)
# │   - salary_min 제거 (급여 조건 완화)
# │   - region이 3글자 이상이면 앞 2글자만 사용 (구→시 수준으로 확대)
# └─ retry_count == 1 (2차 완화)
#     - physical_limit 제거 (신체 제약 조건 완화)
#     - job_type을 유사 직종 리스트로 확장 (job_category_list 사용)


async def param_relaxer_node(state: AgentState) -> dict:
    params = dict(state.get("search_params") or {})
    retry_count = state.get("retry_count", 0)

    # ── 무의미한 region 사전 제거 ────────────────────────────────
    _VAGUE_REGIONS = {"집", "집근처", "근처", "동네", "우리동네", "가까운곳"}
    region_raw = params.get("region", "")
    if region_raw:
        region_normalized = region_raw.replace(" ", "")
        if region_normalized in _VAGUE_REGIONS or len(region_normalized) <= 1:
            params.pop("region", None)
            print(f"[ParamRelax] 무의미한 region '{region_raw}' 제거")

    if retry_count == 0:
        # ── 1차 완화: 급여 제거 + 지역 광역화 ─────────────────────
        params.pop("salary_min", None)

        region = params.get("region", "")
        if region and len(region) >= 3:
            # "강남구" → "강남", "서울 강남구" → "서울" (공백 기준 첫 토큰)
            params["region"] = region.split()[0][:2]
        print(f"[ParamRelax] 1차 완화 → {params}")

    elif retry_count == 1:
        # ── 2차 완화: physical_limit 제거 ─────────────────────────
        # job_type은 /recommend scoring 엔진의 임베딩 유사도가 유사 직종을 자동 처리
        params.pop("physical_limit", None)
        print(f"[ParamRelax] 2차 완화 → {params}")

    return {
        "search_params": params,
        "retry_count": retry_count + 1,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Job Response Generator Node
# ─────────────────────────────────────────────────────────────────────────────


def _format_job_card(row: dict) -> dict:
    """
    DB row → JobCard dict 변환 (알고리즘 처리, LLM 없음)

    규칙:
      - 값이 있는 필드만 조합, 없으면 None (프론트에서 "미기재" 처리)
      - location: city + district 조합 → 둘 다 없으면 location_raw
      - deadline: deadline_type이 'OPEN'이면 "상시모집", 날짜가 있으면 YYYY-MM-DD
      - work_type: work_type_raw 우선, 없으면 work_type_norm
    """
    # 근무지
    city = (row.get("location_city") or "").strip()
    district = (row.get("location_district") or "").strip()
    if city and district:
        location = f"{city} {district}"
    elif city or district:
        location = city or district
    else:
        location = (row.get("location_raw") or "").strip() or None

    # 마감일
    deadline_type = (row.get("deadline_type") or "").upper()
    deadline_at = row.get("deadline_at")
    if deadline_type == "OPEN":
        deadline = "상시모집"
    elif deadline_at:
        # datetime → "YYYY-MM-DD" 문자열
        deadline = str(deadline_at)[:10]
    else:
        deadline = None

    # 근무형태 (raw 우선)
    work_type = (row.get("work_type_raw") or row.get("work_type_norm") or "").strip() or None

    return {
        "id": str(row["id"]),
        "title": (row.get("title_raw") or "").strip(),
        "company": (row.get("company_raw") or "").strip() or None,
        "location": location,
        "salary": (row.get("salary_raw") or "").strip() or None,
        "work_type": work_type,
        "schedule": (row.get("schedule_raw") or "").strip() or None,
        "deadline": deadline,
        "source_url": row.get("source_url") or None,
        "physical_level": row.get("physical_level") or None,
        "senior_tag": row.get("senior_tag") or None,
        "age_min": row.get("age_min") or None,
        "age_max": row.get("age_max") or None,
    }


# LLM은 공고 상세를 보지 않고 도입 문장만 생성 → 할루시네이션 원천 차단
_intro_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 따뜻하고 친절한 일자리 상담사입니다.

공고 카드는 시스템이 별도로 표시하므로, 당신은 짧은 도입 문장만 작성하세요.

규칙:
- 회사명·급여·위치 등 공고의 구체적인 내용은 절대 언급하지 마세요
- 검색 건수와 검색 조건(지역·직종)만 자연스럽게 언급하세요
- 검색 범위를 넓혀서 찾은 경우(retry_count > 0) 이 사실을 언급하세요
- 1~2문장으로 짧게, 이해하기 쉬운 말투로 작성하세요
- 마지막에 관심 있는 공고가 있는지 자연스럽게 물어보세요
- 반드시 한국어로 답변하세요""",
            ),
            (
                "human",
                """[검색 건수]
{job_count}건

[사용자 조건]
{user_conditions}

[재검색 횟수]
{retry_count}

[대화 기록]
{history}

도입 문장을 작성해주세요.""",
            ),
        ]
    )
    | main_llm
    | StrOutputParser()
)


async def job_response_gen_node(state: AgentState) -> dict:
    jobs = state.get("jobs", [])
    retry_count = state.get("retry_count", 0)

    if not jobs:
        return {
            "response": (
                "조건에 맞는 일자리를 찾지 못했어요. 😢\n" "지역이나 직종 조건을 조금 바꿔볼까요?"
            ),
            "jobs": [],
        }

    # /recommend API가 이미 JobCard 형태로 반환 → 별도 포맷팅 불필요
    job_cards = jobs

    # ── 도입 텍스트: LLM은 건수와 조건만 보고 한두 문장 생성 ───────────
    collected = state["collected_info"]
    intro = await _intro_chain.ainvoke(
        {
            "job_count": len(jobs),
            "user_conditions": collected.model_dump()
            if hasattr(collected, "model_dump")
            else collected,
            "retry_count": retry_count,
            "history": state["history_text"],
        }
    )

    return {
        "response": intro,  # 대화 텍스트 (메모리 저장용)
        "jobs": job_cards,  # 구조화된 카드 목록 (router에서 API 응답으로 전달)
    }
