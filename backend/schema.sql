-- ================================================================
-- GoWork AI Agent - DB 스키마 및 목업 데이터
-- 실행: psql postgresql://localhost:5432/gowork -f backend/schema.sql
-- ================================================================


-- ─── 1. 테이블 생성 ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id           bigserial    PRIMARY KEY,
    name         varchar(50)  NOT NULL,
    age          int,
    phone        varchar(20),
    address      varchar(200),
    created_at   timestamp    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS careers (
    id           bigserial    PRIMARY KEY,
    user_id      bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name varchar(100) NOT NULL,
    start_date   date         NOT NULL,
    end_date     date,                   -- 재직 중이면 null
    is_current   boolean      NOT NULL DEFAULT false,
    job_title    varchar(100),
    description  text
);

CREATE TABLE IF NOT EXISTS certifications (
    id           bigserial    PRIMARY KEY,
    user_id      bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         varchar(100) NOT NULL,
    issued_date  date,
    issuer       varchar(100)
);

CREATE TABLE IF NOT EXISTS language_skills (
    id           bigserial    PRIMARY KEY,
    user_id      bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language     varchar(50)  NOT NULL,  -- 영어, 일본어 …
    level        varchar(20)  NOT NULL   -- 일상회화가능 | 업무가능 | 원어민수준
);

CREATE TABLE IF NOT EXISTS document_skills (
    id           bigserial    PRIMARY KEY,
    user_id      bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool         varchar(30)  NOT NULL   -- 워드 | 한글 | 엑셀 | 파워포인트
);

CREATE TABLE IF NOT EXISTS other_skills (
    id           bigserial    PRIMARY KEY,
    user_id      bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword      varchar(100) NOT NULL   -- 협상능력, 리더십 …
);

CREATE TABLE IF NOT EXISTS user_ratings (
    id           bigserial    PRIMARY KEY,
    reviewer_id  bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score        smallint     NOT NULL CHECK (score BETWEEN 1 AND 5),
    category     varchar(20)  NOT NULL,  -- 성실성 | 전문성 | 소통능력
    rated_at     timestamp    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedbacks (
    id           bigserial    PRIMARY KEY,
    reviewer_id  bigint       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id       varchar(36),
    rating       smallint     CHECK (rating BETWEEN 1 AND 5),
    comment      text        DEFAULT NULL,
    created_at   timestamp    NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS job_posting (
    id               uuid         PRIMARY KEY,
    platform_id      uuid         NOT NULL,
    source_job_id    varchar(100),
    title_raw        varchar(200) NOT NULL,
    company_raw      varchar(100),
    description_raw  text,
    source_url       varchar(500) NOT NULL,
    location_raw     varchar(200),
    location_city    varchar(50),
    location_district varchar(50),
    work_type_raw    text,
    work_type_norm   varchar(20),
    schedule_raw     varchar(200),
    salary_raw       varchar(200),
    salary_type_norm varchar(20),
    salary_min       int,
    salary_max       int,
    age_min          int,
    age_max          int,
    senior_tag       varchar(30),
    physical_level   varchar(10),
    industry_raw     varchar(100),
    industry_norm    varchar(30),
    job_category_raw varchar(100),
    job_category_norm varchar(30),
    task_keywords    text,
    headcount        int,
    education_min    varchar(50),
    career_type      varchar(20),
    apply_method     text,
    period_start     date,
    period_end       date,
    posted_at        date,
    deadline_at      date,
    deadline_type    varchar(20) NOT NULL DEFAULT 'DATE',
    collected_at     timestamp   NOT NULL DEFAULT now(),
    status_norm      varchar(20) NOT NULL DEFAULT 'ACTIVE',
    has_phone        boolean     NOT NULL DEFAULT false,
    phone_masked     varchar(20),
    created_at       timestamp   NOT NULL DEFAULT now(),
    updated_at       timestamp   NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_contact (
    id               uuid         PRIMARY KEY,
    posting_id       uuid         NOT NULL,
    phone_encrypted  varchar(200) NOT NULL,
    phone_type       varchar(20)  NOT NULL,
    department       varchar(100),
    created_at       timestamp    NOT NULL DEFAULT now()
);

-- ─── 2. 인덱스 ──────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_careers_user_id         ON careers (user_id);
CREATE INDEX IF NOT EXISTS idx_certifications_user_id  ON certifications (user_id);
CREATE INDEX IF NOT EXISTS idx_language_skills_user_id ON language_skills (user_id);
CREATE INDEX IF NOT EXISTS idx_document_skills_user_id ON document_skills (user_id);
CREATE INDEX IF NOT EXISTS idx_other_skills_user_id    ON other_skills (user_id);


-- ─── 3. job_posting 목업 데이터 ────────────────────────────────────

INSERT INTO job_posting (
    id, platform_id, title_raw, source_url,
    location_city, location_district, location_raw,
    work_type_raw, work_type_norm, salary_min,
    physical_level, senior_tag, job_category_norm,
    deadline_at, deadline_type, status_norm, collected_at
) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '아파트 경비원 모집', 'https://example.com/job/1',
    '서울', '노원구', '서울 노원구',
    '시간제', 'PART_TIME', 1800000,
    'LOW', 'SENIOR_PREFERRED', '경비/보안',
    CURRENT_DATE + INTERVAL '30 days', 'DATE', 'ACTIVE', now()
),
(
    '22222222-2222-2222-2222-222222222222',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '편의점 아르바이트', 'https://example.com/job/2',
    '부산', '사하구', '부산 사하구',
    '시간제', 'PART_TIME', 1500000,
    'LOW', 'SENIOR_FRIENDLY', '판매/영업',
    CURRENT_DATE + INTERVAL '20 days', 'DATE', 'ACTIVE', now()
),
(
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '청소원 채용', 'https://example.com/job/3',
    '서울', '성북구', '서울 성북구',
    '상시', 'FULL_TIME', 2000000,
    'MID', 'SENIOR_PREFERRED', '청소/환경',
    NULL, 'OPEN', 'ACTIVE', now()
)
ON CONFLICT DO NOTHING;

-- ─── 3. 목업 데이터 ─────────────────────────────────────────────
-- 경력/자격증/보유능력 없는 사용자 10명 (id: 1~10)
-- 경력/자격증/보유능력 있는 사용자 10명 (id: 11~20)

INSERT INTO users (id, name, age, phone, address) VALUES
(1,  '김순자', 68, '010-1111-0001', '서울 노원구 상계동'),
(2,  '이복남', 72, '010-1111-0002', '부산 사하구 괴정동'),
(3,  '박말순', 65, '010-1111-0003', '대구 달서구 본리동'),
(4,  '최갑순', 70, '010-1111-0004', '인천 남동구 구월동'),
(5,  '정옥자', 67, '010-1111-0005', '광주 북구 운암동'),
(6,  '강명자', 73, '010-1111-0006', '대전 서구 도마동'),
(7,  '윤복순', 69, '010-1111-0007', '울산 남구 삼산동'),
(8,  '장두이', 71, '010-1111-0008', '경기 수원시 팔달구'),
(9,  '임금순', 66, '010-1111-0009', '경기 성남시 분당구'),
(10, '한말례', 74, '010-1111-0010', '경기 고양시 덕양구'),
(11, '조성호', 62, '010-2222-0011', '서울 강남구 역삼동'),
(12, '신동철', 58, '010-2222-0012', '서울 마포구 합정동'),
(13, '오현숙', 60, '010-2222-0013', '부산 해운대구 우동'),
(14, '권기남', 63, '010-2222-0014', '대구 수성구 범어동'),
(15, '황미경', 57, '010-2222-0015', '인천 연수구 송도동'),
(16, '송재훈', 61, '010-2222-0016', '광주 서구 화정동'),
(17, '배영희', 59, '010-2222-0017', '대전 유성구 봉명동'),
(18, '유태호', 64, '010-2222-0018', '경기 용인시 기흥구'),
(19, '안정숙', 56, '010-2222-0019', '경기 부천시 원미구'),
(20, '문창식', 65, '010-2222-0020', '경기 안산시 단원구')
ON CONFLICT DO NOTHING;

SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));


-- ─── 4. 경력 데이터 (id: 11~20) ─────────────────────────────────

INSERT INTO careers (user_id, company_name, start_date, end_date, is_current, job_title, description) VALUES
(11, '삼성전자',         '1990-03-01', '2010-02-28', false, '생산기술팀 과장', '반도체 생산라인 공정 관리 및 품질 개선'),
(11, '(주)한국설비',     '2010-05-01', '2022-12-31', false, '설비팀장',        '제조 설비 유지보수 및 팀 관리'),
(12, '대한항공',         '1992-04-01', '2015-03-31', false, '지상직 부장',     '화물 운송 및 지상 운영 총괄'),
(12, '인천공항공사',     '2015-06-01', NULL,         true,  '시설운영 차장',   '공항 시설 운영 및 안전 관리'),
(13, '롯데백화점',       '1995-02-01', '2018-01-31', false, '판매팀 과장',     '매장 운영 및 고객 서비스 관리'),
(13, '이마트',           '2018-03-01', '2023-06-30', false, '매장운영 담당',   '생필품 코너 재고 및 판매 관리'),
(14, '현대자동차',       '1988-05-01', '2012-04-30', false, '영업부 차장',     '법인 영업 및 거래처 관리'),
(14, '기아자동차',       '2012-06-01', '2020-05-31', false, '지점장',          '영업 지점 운영 및 실적 관리'),
(15, '국민은행',         '1998-01-01', '2020-12-31', false, '수석행원',        '여신 심사 및 개인 금융 상담'),
(16, '서울아산병원',     '2000-03-01', '2021-02-28', false, '원무팀 과장',     '환자 접수 및 의무기록 관리'),
(17, '한국전력',         '1993-08-01', '2018-07-31', false, '배전팀 차장',     '배전 설비 운영 및 유지보수'),
(17, '(주)에너지솔루션', '2018-09-01', NULL,         true,  '기술고문',        '전력 설비 기술 자문'),
(18, '포스코',           '1986-03-01', '2008-02-28', false, '제강부 부장',     '제강 공정 운영 및 품질 관리'),
(18, '(주)철강기술',     '2008-04-01', '2023-03-31', false, '공장장',          '중소 철강 제조 공장 총괄'),
(19, 'KT',              '1995-06-01', '2019-05-31', false, '네트워크팀 과장', '유무선 네트워크 설치 및 유지보수'),
(20, '서울시청',         '1990-07-01', '2020-06-30', false, '행정 6급',        '민원 처리 및 지역 행정 업무')
ON CONFLICT DO NOTHING;


-- ─── 5. 자격증 데이터 (id: 11~20) ───────────────────────────────

INSERT INTO certifications (user_id, name, issued_date, issuer) VALUES
(11, '기계정비산업기사',   '2005-08-20', '한국산업인력공단'),
(11, '지게차운전기능사',   '2008-04-15', '한국산업인력공단'),
(12, '위험물산업기사',     '2003-06-10', '한국산업인력공단'),
(13, '유통관리사 2급',     '2010-11-05', '대한상공회의소'),
(14, '자동차운전면허 1종', '1990-03-22', '경찰청'),
(14, '세일즈전문가',       '2015-09-01', '한국영업협회'),
(15, '은행텔러 1급',       '2005-05-20', '금융연수원'),
(15, '재경관리사',         '2012-03-15', '한국공인회계사회'),
(16, '병원행정사',         '2008-07-30', '대한병원행정관리자협회'),
(17, '전기기능사',         '2000-11-25', '한국산업인력공단'),
(17, '전기공사산업기사',   '2005-06-18', '한국산업인력공단'),
(18, '용접기능사',         '1998-09-10', '한국산업인력공단'),
(18, '품질경영기사',       '2003-12-05', '한국산업인력공단'),
(19, '정보처리기사',       '2002-07-20', '한국산업인력공단'),
(19, '네트워크관리사 2급', '2007-04-12', '한국정보통신자격협회'),
(20, '행정사',             '2015-03-01', '행정안전부')
ON CONFLICT DO NOTHING;


-- ─── 6. 어학 능력 데이터 (id: 11~20 일부) ───────────────────────

INSERT INTO language_skills (user_id, language, level) VALUES
(11, '영어',   '일상회화가능'),
(12, '영어',   '업무가능'),
(12, '일본어', '일상회화가능'),
(13, '중국어', '일상회화가능'),
(15, '영어',   '업무가능'),
(19, '영어',   '업무가능'),
(20, '영어',   '일상회화가능')
ON CONFLICT DO NOTHING;


-- ─── 7. 문서 툴 능력 데이터 (id: 11~20 일부) ────────────────────

INSERT INTO document_skills (user_id, tool) VALUES
(11, '엑셀'), (11, '파워포인트'),
(12, '워드'), (12, '엑셀'), (12, '파워포인트'),
(13, '한글'), (13, '엑셀'),
(14, '엑셀'), (14, '파워포인트'),
(15, '워드'), (15, '엑셀'), (15, '한글'),
(16, '한글'), (16, '엑셀'),
(17, '엑셀'),
(18, '한글'),
(19, '워드'), (19, '엑셀'), (19, '파워포인트'),
(20, '한글'), (20, '엑셀'), (20, '파워포인트')
ON CONFLICT DO NOTHING;


-- ─── 8. 기타 역량 데이터 (id: 11~20 일부) ───────────────────────

INSERT INTO other_skills (user_id, keyword) VALUES
(11, '설비관리'), (11, '공정개선'), (11, '팀관리'),
(12, '물류관리'), (12, '안전관리'),
(13, '고객응대'), (13, '재고관리'),
(14, '협상능력'), (14, '리더십'), (14, '영업전략'),
(15, '재무분석'), (15, '고객상담'),
(16, '의료행정'), (16, '민원처리'),
(17, '전력설비'), (17, '유지보수'),
(18, '생산관리'), (18, '품질관리'), (18, '원가절감'),
(19, '네트워크'), (19, '장애처리'),
(20, '행정업무'), (20, '문서작성'), (20, '민원처리')
ON CONFLICT DO NOTHING;
