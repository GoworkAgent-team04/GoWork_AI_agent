# GoWork AI Agent — 아키텍처 구조 문서

## 전체 흐름 요약

```
Flutter App (Frontend)
    │
    │  POST /chat  { user_id, message }
    ▼
FastAPI (Backend)
    │
    │  process_message(user_id, message)
    ▼
LangGraph Agent
    ├─ setup_node          : 유저 프로필 로드 + 의도 분류 + 조건 추출
    ├─ profile_checker_node: 검색 파라미터 추출 (LLM)
    ├─ job_searcher_node   : GET /recommend API 호출
    ├─ job_response_gen_node: 응답 생성 (LLM)
    └─ ... (기타 노드)
         │
         │  GET /recommend?user_id=...&region=...&job_type=...
         ▼
    FastAPI /recommend
         │
         ▼
    Scoring Engine (sentence-transformers)
         │
         ▼
    JobCard top3 반환
```

---

## 1. Frontend (Flutter)

### 구조

```
frontend/lib/
├── main.dart                  # 앱 진입점, Provider 주입
├── app.dart                   # MaterialApp 설정
├── constants/
│   └── app_colors.dart        # 색상 상수
├── models/
│   ├── chat_message.dart      # ChatMessage, MessageType, MessageSender
│   ├── chat_session.dart      # ChatSession (세션 단위 대화)
│   └── job_posting.dart       # JobPosting (공고 카드 모델)
├── providers/
│   └── chat_provider.dart     # 상태 관리 (ChangeNotifier)
├── screens/
│   └── chat_screen.dart       # 메인 채팅 화면
├── services/
│   └── chat_api_service.dart  # 백엔드 HTTP 통신
└── widgets/
    ├── bottom_nav_bar.dart    # 하단 내비게이션
    ├── chat_drawer.dart       # 대화 세션 목록 (사이드 드로어)
    ├── chat_input_bar.dart    # 메시지 입력창
    ├── job_card.dart          # 공고 카드 위젯
    └── message_bubble.dart    # 말풍선 위젯 (text / jobRecommendation / loading)
```

### 데이터 흐름

```
사용자 입력
    │
ChatInputBar → ChatProvider.sendMessage()
    │
    │  POST /chat { user_id: 1, message: "서울에서 경비 일 구해요" }
    ▼
ChatApiService.sendMessage()
    │
    ▼
ChatApiResponse { userId, text, jobs: List<JobPosting> }
    │
ChatProvider → ChatSession.messages 에 ChatMessage 추가
    │
    ▼
MessageBubble 렌더링
  - jobs.isEmpty  → MessageType.text
  - jobs.isNotEmpty → MessageType.jobRecommendation → JobCard 위젯 표시
```

### 주요 모델

| 모델 | 역할 |
|---|---|
| `ChatMessage` | 메시지 단위. `type`: text / jobRecommendation / loading |
| `ChatSession` | 대화 세션 단위. 제목 + 메시지 목록 |
| `JobPosting` | 공고 카드. `id, title, company, location, salary, ...` |

### API 호출 방식

- `POST /chat` → 일반 대화 / 추천 모두 처리
- `GET /recommend` → 직접 추천 (파라미터 지정 시)
- base URL: `http://localhost:8000` (하드코딩, `.env` 설정 필요)

---

## 2. Backend (FastAPI)

### 구조

```
backend/
├── main.py                    # FastAPI 앱 설정, 라우터 등록, Flutter 정적 서빙
├── config.py                  # 환경변수 설정 (DB URL, API_BASE_URL 등)
├── schema.sql                 # DB 스키마 (users, careers, job_posting 등)
├── routers/
│   ├── chat.py                # POST /chat, POST /chat/stream, DELETE /chat/history
│   ├── user.py                # GET /users/{user_id}
│   ├── recommend.py           # GET /recommend
│   └── feedback.py            # POST /feedback
├── services/
│   ├── user_service.py        # 유저 프로필 조합 (경력·자격증·스킬 포함)
│   └── recommend_service.py   # 스코어링 + top3 선택
├── repositories/
│   ├── user_repository.py     # users / careers / skills ORM 조회
│   ├── job_repository.py      # job_posting ORM 조회 + 필터링
│   └── feedback_repository.py # feedbacks 저장
├── scoring/
│   ├── weights.py             # Weights 데이터클래스 (항목별 가중치)
│   ├── category.py            # text_similarity() — sentence-transformers 코사인 유사도
│   └── scorer.py              # calc_raw_score(), calc_max_score(), normalize()
├── schemas/
│   ├── chat.py                # ChatRequestDTO, ChatResponseDTO
│   ├── user.py                # UserResponseDTO (id, name, careers, skills 등)
│   ├── job.py                 # JobRequestDTO, JobCard, JobResponseDTO
│   └── feedback.py            # FeedbackRequestDTO, FeedbackResponseDTO
├── models/
│   └── orm.py                 # SQLAlchemy ORM 모델 (User, Career, JobPosting 등)
└── database/
    ├── connection.py          # SQLAlchemy engine + SessionLocal
    └── queries.py             # 레거시 raw SQL (에이전트 노드에서 직접 사용)
```

### API 엔드포인트

| 메서드 | 경로 | 역할 |
|---|---|---|
| `POST` | `/chat` | 메시지 전송 → LangGraph 에이전트 실행 → 응답 + 공고 반환 |
| `POST` | `/chat/stream` | 응답 스트리밍 (공고 카드 미포함) |
| `DELETE` | `/chat/history` | 대화 기록 초기화 |
| `GET` | `/users/{user_id}` | 유저 프로필 조회 (경력·자격증·스킬 포함) |
| `GET` | `/recommend` | 스코어링 기반 공고 top3 추천 |
| `POST` | `/feedback` | 공고 피드백 저장 |

### 스코어링 엔진 (`/recommend` 처리 흐름)

```
GET /recommend?user_id=1&region=서울&job_type=경비&physical_limit=true

1. job_repository.search_jobs()
   └─ Hard Filter: region(ILIKE) + physical_limit(LOW/MID)
   └─ 후보 최대 50개 조회 (JOB_CANDIDATE_POOL)

2. scoring.calc_raw_score(job, params)
   └─ job_type    : sentence-transformers 코사인 유사도 × 0.35
   └─ physical_level: rule-based (일치 여부) × 0.25
   └─ work_type   : rule-based × 0.20
   └─ salary_min  : rule-based × 0.20
   └─ senior_tag  : 항상 평가 × 0.20

3. normalize(raw_score / max_score) → 0~1 rank score

4. 내림차순 정렬 → top3 JobCard 반환
```

---

## 3. LangGraph Agent (LLM 노드)

### 그래프 구조

```
START
  └─ setup_node
       ├─ JOB_RECOMMEND   → profile_checker_node
       │      ├─ 정보 부족  → question_gen_node → END
       │      └─ 정보 충분  → job_searcher_node
       │              ├─ 결과 ≥ 3건  → job_response_gen_node → END
       │              └─ 결과 부족   → param_relaxer_node
       │                     ├─ retry < 2 → job_searcher_node (루프)
       │                     └─ retry ≥ 2 → job_response_gen_node → END
       ├─ JOB_INQUIRY     → job_inquiry_node  → END
       ├─ JOB_APPLY       → job_apply_node    → END
       ├─ PROFILE         → profile_handler_node → END
       └─ GENERAL_CHAT    → general_chat_node → END
```

### 노드별 역할

#### `setup_node`
```
매 요청의 첫 번째 노드. 아래 3가지를 asyncio.gather로 동시 실행:

① _extract_profile(user_message)
   fast_llm → 메시지에서 { job_type, region, physical_limit, work_type, salary_min } 추출

② classify_intent(user_message, history)
   fast_llm → 의도 분류
   { JOB_RECOMMEND / JOB_INQUIRY / JOB_APPLY / PROFILE / GENERAL_CHAT }

③ _fetch_user_profile(user_id)
   GET /users/{user_id} HTTP 호출
   → { id, name, age, careers, certifications, skills } → db_profile로 state 주입
```

#### `profile_checker_node`
```
region 충족 여부 코드 판단 (LLM 없음)
  └─ collected_info 또는 db_profile에 지역 있으면 충분

정보 충분 시 → _param_extractor_chain (fast_llm)
  입력: db_profile + collected_info + history
  출력: JobSearchParams JSON
    { region, job_type, physical_limit, work_type, salary_min }
```

#### `job_searcher_node`
```
GET /recommend HTTP 호출 (httpx)
  파라미터: user_id + search_params (LLM이 추출한 JSON)
  응답: JobCard top3 (scoring 엔진 적용 완료)
```

#### `param_relaxer_node`
```
결과 부족 시 파라미터 완화 후 재검색

retry_count == 0 (1차 완화)
  └─ salary_min 제거
  └─ region 광역화 ("강남구" → "강남")

retry_count == 1 (2차 완화)
  └─ physical_limit 제거
  └─ job_type 유지 (scoring 엔진 임베딩 유사도가 유사 직종 자동 처리)
```

#### `job_response_gen_node`
```
공고 카드: /recommend API 응답이 이미 JobCard 형태 → 그대로 사용
도입 텍스트: main_llm → 건수 + 조건만 보고 1~2문장 생성 (할루시네이션 방지)
```

#### `job_inquiry_node`
```
"이 공고 전화번호가 어떻게 돼요?" 같은 공고 문의 처리
LLM이 last_jobs에서 공고 ID 파악 → DB 상세 조회 → 응답 생성
```

#### `job_apply_node`
```
지원 처리
LLM이 공고 ID 파악 → 중복 지원 체크 → applications 테이블에 저장
```

#### `profile_handler_node`
```
READ   : 프로필 조회 후 LLM이 안내
UPDATE : 사용자가 직접 수정 요청
COLLECT: 대화 중 수집된 정보를 DB에 자동 저장
```

### 메모리 구조

```python
ConversationMemory {
  _histories  : { user_id → [HumanMessage, AIMessage, ...] }  # 최근 10턴
  _profiles   : { user_id → ProfileInfo(job_type, region, ...) }  # 대화 누적
  _last_jobs  : { user_id → [JobCard, ...] }  # 마지막 추천 공고
}
```

### AgentState (LangGraph 공유 상태)

```python
AgentState {
  # 입력
  user_id, user_message

  # setup_node 출력
  history_text, history_messages   # 대화 기록
  collected_info                   # 누적 수집 정보 (ProfileInfo)
  db_profile                       # GET /users/{user_id} 응답
  extracted_info                   # 이번 메시지에서 새로 추출된 정보
  intent                           # 의도

  # 추천 파이프라인
  search_params                    # LLM이 추출한 검색 파라미터 JSON
  jobs                             # GET /recommend 응답 (JobCard 목록)
  retry_count                      # 파라미터 완화 재시도 횟수
  is_info_sufficient               # 정보 충족 여부
  missing_fields                   # 부족한 필드 목록

  # 최종 출력
  response                         # LLM 생성 텍스트
}
```

---

## 4. 데이터베이스 스키마 요약

```
users          : id, name, age, phone, address
careers        : user_id, company_name, job_title, start_date, end_date, is_current
certifications : user_id, name, issued_date
language_skills: user_id, language, level
document_skills: user_id, tool
other_skills   : user_id, keyword
feedbacks      : user_id, job_id, rating, comment
job_posting    : id(uuid), title_raw, company_raw, location_*, salary_*, work_type_*,
                 physical_level, senior_tag, age_min, age_max, source_url, deadline_*
job_contact    : posting_id, phone_type, department
```

---

## 5. 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///jobs.db` | PostgreSQL URL |
| `GROQ_API_KEY` | - | LLM API 키 |
| `API_BASE_URL` | `http://localhost:8000` | 에이전트 → 백엔드 API 호출 URL |
| `JOB_CANDIDATE_POOL` | `50` | 스코어링 후보 최대 조회 수 |
| `MAX_JOB_RESULTS` | `5` | 에이전트 재검색 루프 임계값 |

---

## 6. 로컬 실행

```bash
# 1. 백엔드 실행
uvicorn backend.main:app --reload --port 8000

# 2. Flutter 웹 빌드 (선택)
cd frontend && flutter build web --release
# → frontend/build/web/ 생성 → FastAPI가 / 경로로 정적 서빙

# 3. Flutter 앱 실행 (개발)
cd frontend && flutter run -d chrome
```
