-- ================================================================
-- users (임시) + applications 테이블 생성
-- 실행: psql postgresql://minki:1234@localhost:5432/gowork -f migrations/create_users_and_applications.sql
-- ================================================================


-- ─── 1. application_status enum 생성 ────────────────────────────

CREATE TYPE application_status AS ENUM (
    'PENDING',    -- 지원 완료 (검토 대기)
    'VIEWED',     -- 업체가 이력서 열람
    'PASS',       -- 합격
    'FAIL',       -- 불합격
    'CANCELLED'   -- 사용자가 취소
);


-- ─── 2. users 테이블 (임시) ──────────────────────────────────────
-- 실제 users 테이블은 회사 구현 기준을 따름
-- 이 테이블은 AI 에이전트 개발/테스트 용도

CREATE TABLE IF NOT EXISTS users (
    id                   uuid          NOT NULL DEFAULT uuid_generate_v4(),
    name                 varchar(50)   NOT NULL,
    phone_encrypted      varchar(500),                        -- 암호화된 전화번호
    birth_year           smallint,                            -- 출생연도 (나이 계산용)
    region_city          varchar(30),                         -- 거주 시/도
    region_district      varchar(50),                         -- 거주 구/군
    preferred_job_category job_category,                      -- 희망 직종
    preferred_work_type  work_type,                           -- 희망 근무형태
    physical_level       physical_level DEFAULT 'HIGH',       -- 신체 활동 가능 수준
    career_type          career_type    DEFAULT 'UNKNOWN',    -- 경력 유형
    experience_desc      text,                                -- 경력 상세 설명
    is_active            boolean        NOT NULL DEFAULT true, -- 계정 활성 여부
    created_at           timestamp      NOT NULL DEFAULT now(),
    updated_at           timestamp      NOT NULL DEFAULT now(),

    CONSTRAINT users_pkey PRIMARY KEY (id)
);

COMMENT ON TABLE  users                          IS '사용자 프로필 (임시 테이블 - 실제 구현으로 교체 필요)';
COMMENT ON COLUMN users.physical_level           IS 'LOW: 가벼운 업무만 가능 / MID: 보통 / HIGH: 제약 없음';
COMMENT ON COLUMN users.preferred_job_category   IS 'job_category enum 참고';


-- ─── 3. applications 테이블 ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS applications (
    id           uuid               NOT NULL DEFAULT uuid_generate_v4(),
    user_id      uuid               NOT NULL,
    posting_id   uuid               NOT NULL,
    status       application_status NOT NULL DEFAULT 'PENDING',
    memo         text,                                        -- 사용자 메모 (선택)
    applied_at   timestamp          NOT NULL DEFAULT now(),
    updated_at   timestamp          NOT NULL DEFAULT now(),

    CONSTRAINT applications_pkey          PRIMARY KEY (id),
    CONSTRAINT applications_user_fkey     FOREIGN KEY (user_id)    REFERENCES users (id),
    CONSTRAINT applications_posting_fkey  FOREIGN KEY (posting_id) REFERENCES job_posting (id),
    CONSTRAINT applications_unique        UNIQUE (user_id, posting_id)  -- 중복 지원 방지
);

COMMENT ON TABLE  applications        IS '사용자 지원 이력';
COMMENT ON COLUMN applications.status IS 'PENDING: 대기 / VIEWED: 열람 / PASS: 합격 / FAIL: 불합격 / CANCELLED: 취소';


-- ─── 4. 인덱스 ──────────────────────────────────────────────────

CREATE INDEX idx_applications_user    ON applications (user_id);
CREATE INDEX idx_applications_posting ON applications (posting_id);
CREATE INDEX idx_applications_status  ON applications (status);
CREATE INDEX idx_users_region         ON users (region_city, region_district);


-- ─── 5. 테스트 데이터 (개발용) ───────────────────────────────────

INSERT INTO users (
    id, name, birth_year, region_city, region_district,
    preferred_job_category, preferred_work_type, physical_level, career_type
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    '테스트사용자',
    1960,
    '서울',
    '강남구',
    'SECURITY',
    'PART_TIME',
    'MID',
    'EXPERIENCED'
)
ON CONFLICT DO NOTHING;
