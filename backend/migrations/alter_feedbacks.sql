-- ================================================================
-- feedbacks 테이블 구조 변경
-- rating, job_id 컬럼 추가 / content → comment 로 변경
-- 실행: psql postgresql://localhost:5432/gowork -f backend/migrations/alter_feedbacks.sql
-- ================================================================

ALTER TABLE feedbacks
    ADD COLUMN IF NOT EXISTS job_id  varchar(36),
    ADD COLUMN IF NOT EXISTS rating  smallint CHECK (rating BETWEEN 1 AND 5);

ALTER TABLE feedbacks
    RENAME COLUMN content TO comment;
