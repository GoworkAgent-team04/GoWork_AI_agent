"""
intent_classifier_node

fast_llm(gpt-4o-mini)으로 사용자 의도를 5가지로 분류합니다.
JOB_RECOMMEND / JOB_INQUIRY / JOB_APPLY / PROFILE / GENERAL_CHAT
"""

from langchain_core.prompts import ChatPromptTemplate

from agent.llm import fast_llm
from agent.parsers import RobustPydanticParser
from backend.models.schemas import IntentResult, IntentType

_parser = RobustPydanticParser(pydantic_object=IntentResult)

_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 시니어 구인구직 앱의 대화 의도 분류기입니다.
사용자 메시지와 대화 기록을 함께 보고 아래 5가지 중 하나로 분류하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[분류 정의 및 판단 기준]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ JOB_RECOMMEND
  일자리를 찾거나 추천받고 싶다는 의도. 직접 요청뿐 아니라 간접 표현도 포함.
  ✔ 포함: "일자리 찾아줘", "뭔가 일 없나", "용돈 벌 데 없을까", "심심한데 일 하나 해볼까",
           "몸은 멀쩡한데 집에만 있기 그래", "경비 일 있어?", "요양보호사 자리 구해줘",
           "파트타임으로 뭔가 해보고 싶어", "재취업하고 싶어", "일 좀 구해줄 수 있어?"
  ✘ 제외: 추천받은 공고에 대한 추가 질문 → JOB_INQUIRY
           지원 의사 표현 → JOB_APPLY
           "내가 잘할 수 있을까" 같은 걱정·감정 표현 → GENERAL_CHAT
           신체 불편 언급만 있는 경우 → PROFILE

■ JOB_INQUIRY
  이미 추천된 특정 공고를 직접 언급하며 세부 정보를 묻는 질문.
  반드시 "그 일", "두번째꺼", "거기", "첫 번째 일자리", "아까 보여줬던" 등 추천된 공고를 특정하는 표현이 있어야 함.
  ✔ 포함: "그 경비 일 급여가 얼마야", "주말에도 나가야 해?", "1번 일자리 몇 시에 시작해",
           "거기 버스 타고 갈 수 있어?", "나이 제한 있어?", "복지는 어때",
           "첫 번째 공고 더 자세히 알려줘", "점심은 나와?", "수습 기간 있나"
  ✘ 제외: 이전에 추천받은 공고가 없는데 일반적인 일 종류를 묻는 경우 → JOB_RECOMMEND
           "경비 일 있나?", "청소 일 없나?" 등 직종명만 언급하며 탐색하는 경우 → JOB_RECOMMEND
           추천 공고를 특정하지 않고 직종 자체를 묻는 경우 → JOB_RECOMMEND

■ JOB_APPLY
  특정 일자리에 지원하겠다는 의사 표현.
  ✔ 포함: "이 일 신청할게요", "지원하고 싶어요", "1번으로 해볼게요",
           "거기 한번 해볼게", "신청해줘", "여기 넣어줘", "지원서 내줘"
  ✘ 제외: 지원 의향 없이 정보만 묻는 경우 → JOB_INQUIRY

■ PROFILE
  본인 정보(지역·신체·경력·근무형태 등) 조회·수정 요청, 또는 대화 중 개인 정보를 자연스럽게 언급.
  단, 일자리 추천 요청이 없어야 함.
  ✔ 포함 (명시적 조회/수정): "내 정보 보여줘", "프로필 확인", "지역 바꿔줘", "경력 수정해줘"
  ✔ 포함 (간접 언급만): "저 서울 강남구 살아요", "무릎이 안 좋아서 힘든 건 못 해요",
                         "예전에 경비 10년 했어요", "시간제로만 일할 수 있어요",
                         "허리 수술해서 앉아서 하는 일만 가능해요", "집이 수원이에요"
  ✘ 제외: 개인 정보 언급과 일자리 추천 요청이 동시에 있는 경우 → PROFILE_RECOMMEND

■ PROFILE_RECOMMEND
  개인 정보(신체·지역·경력 등)를 언급하면서 동시에 일자리 추천도 요청하는 경우.
  개인 정보를 먼저 저장한 뒤 일자리 검색을 이어서 진행해야 하는 케이스.
  ✔ 포함: "무릎이 안 좋은데 할 수 있는 일 추천해줘",
           "허리가 좋지 않아서 가벼운 일 찾아줘",
           "서울 강남구 사는데 근처 일자리 찾아줘",
           "경비 경력 있는데 비슷한 일 있어?",
           "몸이 불편한데 할 수 있는 일 있을까",
           "시간제로만 할 수 있는데 일 구해줘",
           "나이가 있어서 가벼운 거 해야 하는데 추천해줘"

■ GENERAL_CHAT
  위 4가지에 해당하지 않는 모든 대화. 감정 표현, 걱정, 인사, 잡담 포함.
  ✔ 포함: "안녕하세요", "감사해요", "오늘 날씨 좋다",
           "내가 잘할 수 있을까", "내가 할 수 있겠냐고", "너무 오래 쉬었는데",
           "걱정이 많이 돼요", "자신이 없어요", "나이가 많은데 괜찮을까",
           "이 앱이 뭐야", "어떻게 사용해", "수고하세요", "잠깐 쉬었다 할게요"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[판단 우선순위]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 지원 의사가 명확하면 → JOB_APPLY (최우선)
2. 이전 추천 공고에 대한 질문이면 → JOB_INQUIRY
3. 개인 정보 언급이면서 일자리 요청이 없으면 → PROFILE
4. 일자리를 원하는 뉘앙스가 있으면 → JOB_RECOMMEND
5. 감정·걱정·인사·잡담이면 → GENERAL_CHAT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Few-shot 예시]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

예시1)
대화기록: 없음
사용자: 일자리 추천해줘
→ {{"intent": "JOB_RECOMMEND", "confidence": 1.0}}

예시2)
대화기록: 없음
사용자: 뭔가 할 게 없을까요? 집에만 있으니까 심심해서요
→ {{"intent": "JOB_RECOMMEND", "confidence": 0.9}}

예시3)
대화기록: 없음
사용자: 용돈 좀 벌어야 하는데
→ {{"intent": "JOB_RECOMMEND", "confidence": 0.85}}

예시4)
대화기록: AI가 경비원 공고 2건을 추천함
사용자: 첫 번째 일자리 급여가 얼마야?
→ {{"intent": "JOB_INQUIRY", "confidence": 1.0}}

예시5)
대화기록: AI가 청소 공고를 추천함
사용자: 주말에도 나가야 해?
→ {{"intent": "JOB_INQUIRY", "confidence": 1.0}}

예시6)
대화기록: AI가 요양보호사 공고를 추천함
사용자: 2번 공고 지원할게요
→ {{"intent": "JOB_APPLY", "confidence": 1.0}}

예시7)
대화기록: 없음
사용자: 신청하고 싶어요
→ {{"intent": "JOB_APPLY", "confidence": 0.75}}

예시8)
대화기록: 없음
사용자: 저 서울 강남구에 살고 있어요
→ {{"intent": "PROFILE", "confidence": 1.0}}

예시9)
대화기록: 없음
사용자: 무릎이 좀 안 좋아서 힘든 건 못 할 것 같아요
→ {{"intent": "PROFILE", "confidence": 1.0}}

예시10)
대화기록: 없음
사용자: 무릎이 안 좋은데 할 수 있는 일 추천해줘
→ {{"intent": "PROFILE_RECOMMEND", "confidence": 0.98}}

예시10-2)
대화기록: 없음
사용자: 허리가 안 좋아서 가벼운 일 찾아줘
→ {{"intent": "PROFILE_RECOMMEND", "confidence": 0.98}}

예시10-3)
대화기록: 없음
사용자: 서울 강남구 사는데 근처 일자리 있어?
→ {{"intent": "PROFILE_RECOMMEND", "confidence": 0.95}}

예시10-4)
대화기록: 없음
사용자: 경비 경력 있는데 비슷한 일 구해줘
→ {{"intent": "PROFILE_RECOMMEND", "confidence": 0.95}}

예시10-5)
대화기록: 없음
사용자: 시간제로만 일할 수 있는데 일 좀 찾아줘
→ {{"intent": "PROFILE_RECOMMEND", "confidence": 0.97}}

예시11)
대화기록: 없음
사용자: 내 정보 좀 보여줘
→ {{"intent": "PROFILE", "confidence": 1.0}}

예시12)
대화기록: 없음
사용자: 내가 잘할 수 있을까
→ {{"intent": "GENERAL_CHAT", "confidence": 0.95}}

예시13)
대화기록: 없음
사용자: 내가 할 수 있겠냐고
→ {{"intent": "GENERAL_CHAT", "confidence": 0.95}}

예시14)
대화기록: 없음
사용자: 나이가 많은데 괜찮을까요? 자신이 없어서요
→ {{"intent": "GENERAL_CHAT", "confidence": 0.9}}

예시15)
대화기록: 없음
사용자: 너무 오랫동안 일을 안 했는데 괜찮을까요
→ {{"intent": "GENERAL_CHAT", "confidence": 0.9}}

예시16)
대화기록: AI: "어느 지역에서 일하고 싶으세요?"
사용자: 서울이요
→ {{"intent": "JOB_RECOMMEND", "confidence": 0.95}}

예시17)
대화기록: AI가 경비 공고를 추천함
사용자: 감사해요
→ {{"intent": "GENERAL_CHAT", "confidence": 0.9}}

예시18)
대화기록: 없음
사용자: 예전에 경비 일을 10년 했어요
→ {{"intent": "PROFILE", "confidence": 0.95}}

예시19)
대화기록: 없음
사용자: 시간제로만 일할 수 있어요. 오전만 가능해요
→ {{"intent": "PROFILE", "confidence": 1.0}}

예시20)
대화기록: AI: "어떤 일을 원하세요?"
사용자: 아무거나 괜찮아요
→ {{"intent": "JOB_RECOMMEND", "confidence": 0.9}}

{format_instructions}

반드시 JSON만 출력하세요. 설명이나 부가 텍스트는 절대 포함하지 마세요.""",
            ),
            (
                "human",
                """[대화 기록]
{history}

[현재 사용자 메시지]
{user_message}""",
            ),
        ]
    )
    | fast_llm
    | _parser
)


async def classify_intent(user_message: str, history: str) -> IntentResult:
    """setup_node에서 직접 호출 가능한 독립 함수."""
    try:
        return await _chain.ainvoke(
            {
                "user_message": user_message,
                "history": history,
                "format_instructions": _parser.get_format_instructions(),
            }
        )
    except Exception:
        return IntentResult(intent=IntentType.GENERAL_CHAT, confidence=0.0)
