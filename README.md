# GoWork AI Agent

시니어(고령자) 대상 AI 일자리 추천 챗봇 서비스.
대화를 통해 사용자의 조건(지역, 직종, 신체 조건 등)을 파악하고, 임베딩 기반 스코어링으로 맞춤 공고를 추천한다.

---

## 개요

| 항목 | 내용 |
|------|------|
| 타겟 | 50~70대 시니어 구직자 |
| 인터페이스 | Flutter 앱 (Android / iOS / Web) |
| 백엔드 | Python FastAPI + LangGraph 에이전트 |
| LLM | Groq API (fast: llama-3.1-8b-instant / main: llama-3.3-70b-versatile) |
| DB | PostgreSQL (AWS RDS db.t3.micro) |
| 배포 | AWS EC2 t3.medium, GitHub Actions CD |

### 핵심 흐름

```
Flutter 앱
    │  POST /chat { user_id, message }
    ▼
FastAPI
    │  process_message()
    ▼
LangGraph Agent
    ├─ setup_node      : 의도 분류 + 프로필/조건 추출 (8b)
    ├─ profile_checker : 검색 파라미터 확정 (8b)
    ├─ job_searcher    : GET /recommend 호출
    └─ job_response    : 응답 텍스트 생성 (70b)
         │  top3 JobCard + 텍스트
         ▼
Flutter 앱 (말풍선 + 공고 카드)
```

---

## 전체 디렉토리 구조

```
GoWork_AI_agent/
│
├── backend/                        # FastAPI 서버
│   ├── main.py                     # 앱 진입점, 라우터 등록, Flutter 정적 서빙
│   ├── config.py                   # 환경변수 (DB URL, 모델명, API KEY 등)
│   ├── schema.sql                  # DB 스키마 + 목업 데이터
│   │
│   ├── routers/                    # API 엔드포인트
│   │   ├── chat.py                 # POST /chat, DELETE /chat/history
│   │   ├── recommend.py            # GET /recommend (스코어링 추천)
│   │   └── user.py                 # GET /users/{user_id}
│   │
│   ├── services/                   # 비즈니스 로직
│   │   ├── recommend_service.py    # 스코어링 + top3 선택
│   │   └── user_service.py         # 유저 프로필 조합
│   │
│   ├── repositories/               # DB 접근 계층
│   │   ├── job_repository.py       # job_posting ORM 조회 + 필터링
│   │   ├── user_repository.py      # users / careers / skills 조회
│   │   └── chat_repository.py      # chat_sessions / chat_messages 저장
│   │
│   ├── scoring/                    # 임베딩 스코어링 엔진
│   │   ├── scorer.py               # calc_raw_score(), normalize()
│   │   ├── category.py             # text_similarity() (코사인 유사도)
│   │   └── weights.py              # 항목별 가중치 설정
│   │
│   ├── models/
│   │   └── orm.py                  # SQLAlchemy ORM 모델
│   │
│   ├── schemas/                    # Pydantic 스키마 (요청/응답 DTO)
│   │   ├── chat.py
│   │   ├── job.py
│   │   └── user.py
│   │
│   ├── database/
│   │   ├── connection.py           # SQLAlchemy engine + 세션
│   │   └── queries.py              # 레거시 raw SQL (에이전트 일부 노드에서 사용)
│   │
│   └── tests/                      # 테스트
│       ├── conftest.py
│       ├── routers/                # 라우터 단위 테스트
│       ├── scoring/                # 스코어링 단위 테스트
│       └── integration/            # 통합 테스트 (실 DB)
│
├── agent/                          # LangGraph 에이전트
│   ├── graph.py                    # StateGraph 정의 (노드 연결 + 엣지)
│   ├── state.py                    # AgentState 타입 정의
│   ├── llm.py                      # fast_llm(8b) / main_llm(70b) 초기화
│   ├── memory.py                   # 인메모리 대화 기록 + 누적 프로필
│   ├── router.py                   # process_message() — 그래프 실행 진입점
│   ├── prompt.py                   # 시스템 프롬프트 모음
│   ├── parsers.py                  # LLM 출력 파서
│   ├── llm_logger.py               # LLM 호출 로깅 콜백
│   │
│   └── nodes/                      # 그래프 노드
│       ├── setup.py                # 의도 분류 + 조건 추출 (매 요청 첫 노드)
│       ├── intent.py               # classify_intent() 함수
│       ├── profile.py              # PROFILE 의도 처리 (조회/수정/수집)
│       ├── job_recommend.py        # JOB_RECOMMEND 파이프라인
│       │                           # (profile_checker → job_searcher → param_relaxer → response_gen)
│       ├── job_inquiry.py          # 공고 문의 처리 (전화번호, 위치 등)
│       ├── job_apply.py            # 지원 처리
│       └── general_chat.py         # 일반 대화 처리
│
├── frontend/                       # Flutter 앱
│   ├── lib/
│   │   ├── main.dart               # 앱 진입점
│   │   ├── app.dart                # MaterialApp 설정
│   │   ├── constants/
│   │   │   └── app_colors.dart     # 색상 상수
│   │   ├── models/
│   │   │   ├── chat_message.dart   # ChatMessage (type: text / jobRecommendation / loading)
│   │   │   ├── chat_session.dart   # ChatSession (세션 단위 대화)
│   │   │   └── job_posting.dart    # JobPosting (공고 카드 모델)
│   │   ├── providers/
│   │   │   └── chat_provider.dart  # 상태 관리 (ChangeNotifier)
│   │   ├── screens/
│   │   │   └── chat_screen.dart    # 메인 채팅 화면
│   │   ├── services/
│   │   │   └── chat_api_service.dart # 백엔드 HTTP 통신
│   │   └── widgets/
│   │       ├── message_bubble.dart # 말풍선 (텍스트 / 공고카드 / 로딩)
│   │       ├── job_card.dart       # 공고 카드 위젯
│   │       ├── chat_input_bar.dart # 메시지 입력창
│   │       ├── chat_drawer.dart    # 대화 세션 목록 (사이드 드로어)
│   │       └── bottom_nav_bar.dart # 하단 내비게이션
│   └── web/                        # Flutter 웹 빌드 결과 (정적 파일)
│
├── scripts/
│   └── compute_embeddings.py       # 공고 임베딩 사전 계산 스크립트
│
├── docs/
│   └── architecture.md             # 상세 아키텍처 문서
│
├── .github/
│   └── workflows/
│       ├── cd.yml                  # CD 파이프라인 (EC2 rsync 배포)
│       ├── ci.yml                  # CI (ruff, pytest)
│       └── db-migrate.yml          # 수동 DB 마이그레이션 (workflow_dispatch)
│
├── Dockerfile                      # 백엔드 컨테이너 이미지
├── pyproject.toml                  # Python 패키지 설정 (Poetry)
├── BACKEND_CODE_GUIDE.md           # 백엔드 코드 레벨 개발자 가이드
└── README.md
```

---

## 로컬 실행

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env에 DATABASE_URL, GROQ_API_KEY, API_BASE_URL 입력

# 2. 의존성 설치
poetry install

# 3. DB 스키마 적용
psql $DATABASE_URL -f backend/schema.sql

# 4. 임베딩 사전 계산 (최초 1회)
python scripts/compute_embeddings.py

# 5. 서버 실행
uvicorn backend.main:app --reload --port 8000

# 6. Flutter 앱 실행 (개발)
cd frontend && flutter run -d chrome
```

---

## 환경변수

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL |
| `GROQ_API_KEY` | Groq LLM API 키 |
| `API_BASE_URL` | 에이전트 → 백엔드 호출 URL (기본: `http://localhost:8000`) |
| `MAIN_MODEL` | 응답 생성 모델 (기본: `llama-3.3-70b-versatile`) |
| `FAST_MODEL` | 분류/추출 모델 (기본: `llama-3.1-8b-instant`) |

---

## 한계점

### 1. Groq 무료 플랜 TPD 제한
- `llama-3.3-70b-versatile`: 100,000 tokens/day 상한
- 대화 1회당 최소 2번의 LLM 호출(8b + 70b)이 발생하며, 트래픽이 몰리면 당일 한도 소진 가능
- 한도 소진 시 응답이 "잠시 후 다시 말씀해 주세요"로 fallback됨

### 2. 인메모리 대화 기록
- `agent/memory.py`의 대화 기록은 서버 프로세스 메모리에만 저장됨
- 서버 재시작 또는 EC2 재부팅 시 모든 대화 기록 초기화
- `chat_messages` 테이블이 DB에 존재하나 현재 실제 저장/조회에 사용되지 않음

### 3. 마감일 필터 미적용
- `job_repository.py`의 마감일 필터(`deadline_at >= 오늘`)가 주석 처리되어 있음
- 마감된 공고도 추천 결과에 포함될 수 있음

### 4. 공고 데이터 크롤링 미포함
- 공고 수집 크롤러 코드는 별도 레포지토리(또는 파이프라인)에서 관리
- 이 레포의 `job_posting` 테이블은 외부에서 적재된 데이터를 소비하는 구조
- 공고가 갱신되지 않으면 추천 품질이 시간이 지남에 따라 저하됨

### 5. 단일 EC2 인스턴스 단일 장애점
- 로드 밸런서 없이 EC2 1대로 운영 중
- 인스턴스 장애 시 서비스 전체 중단
- 디스크 풀(full) 발생 이력 있음 (임베딩 모델 캐시 + 로그 누적)

### 6. 검색 성능
- `region="서울"` 같은 광역 조건 시 수천 건 DB 조회 + 임베딩 행렬 연산 발생
- 현재 httpx 타임아웃 30초로 설정되어 있으나, 공고 수 증가 시 재조정 필요
- 공고 임베딩은 `scripts/compute_embeddings.py`로 사전 계산되나, 신규 공고 적재 후 재실행 필요

### 7. 사용자 인증 없음
- `user_id`를 정수로 직접 전달하는 구조 (JWT/세션 인증 없음)
- 현재는 목업 사용자 데이터(id: 1~20)로만 테스트 가능
- 실 서비스 전 인증 레이어 추가 필요
