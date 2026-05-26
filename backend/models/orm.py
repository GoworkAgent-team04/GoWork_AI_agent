"""
SQLAlchemy ORM 모델 정의

users / careers / certifications / language_skills /
document_skills / other_skills / feedbacks 테이블 (피그마를 보고 추측)

job_posting / job_contact 은 외부 크롤링 테이블 (읽기 전용).
DB에 정의된 커스텀 enum 타입은 Python 쪽에서 String으로 매핑합니다.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Float,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    age: Mapped[Optional[int]]
    phone: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    company_name: Mapped[str]
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    job_title: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(Text)


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str]
    issued_date: Mapped[Optional[date]] = mapped_column(Date)
    issuer: Mapped[Optional[str]]


class LanguageSkill(Base):
    __tablename__ = "language_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    language: Mapped[str]
    level: Mapped[str]


class DocumentSkill(Base):
    __tablename__ = "document_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tool: Mapped[str]


class OtherSkill(Base):
    __tablename__ = "other_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    keyword: Mapped[str]


class Feedback(Base):
    __tablename__ = "feedbacks"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedbacks_rating"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reviewer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    job_id: Mapped[Optional[str]]
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


# ─── 크롤링 테이블 (읽기 전용) ────────────────────────────────────


class JobPosting(Base):
    __tablename__ = "job_posting"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    platform_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    source_job_id: Mapped[Optional[str]]
    title_raw: Mapped[str]
    company_raw: Mapped[Optional[str]]
    description_raw: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[str]
    location_raw: Mapped[Optional[str]]
    location_city: Mapped[Optional[str]]
    location_district: Mapped[Optional[str]]
    work_type_raw: Mapped[Optional[str]] = mapped_column(Text)
    work_type_norm: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_raw: Mapped[Optional[str]]
    salary_raw: Mapped[Optional[str]]
    salary_type_norm: Mapped[Optional[str]] = mapped_column(String(20))
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    age_min: Mapped[Optional[int]] = mapped_column(Integer)
    age_max: Mapped[Optional[int]] = mapped_column(Integer)
    senior_tag: Mapped[Optional[str]] = mapped_column(String(30))
    physical_level: Mapped[Optional[str]] = mapped_column(String(10))
    industry_raw: Mapped[Optional[str]]
    industry_norm: Mapped[Optional[str]] = mapped_column(String(30))
    job_category_raw: Mapped[Optional[str]]
    job_category_norm: Mapped[Optional[str]] = mapped_column(String(30))
    task_keywords: Mapped[Optional[str]] = mapped_column(Text)
    headcount: Mapped[Optional[int]] = mapped_column(Integer)
    education_min: Mapped[Optional[str]]
    career_type: Mapped[Optional[str]] = mapped_column(String(20))
    apply_method: Mapped[Optional[str]] = mapped_column(Text)
    period_start: Mapped[Optional[date]] = mapped_column(Date)
    period_end: Mapped[Optional[date]] = mapped_column(Date)
    posted_at: Mapped[Optional[date]] = mapped_column(Date)
    deadline_at: Mapped[Optional[date]] = mapped_column(Date)
    deadline_type: Mapped[str] = mapped_column(String(20))
    collected_at: Mapped[datetime]
    status_norm: Mapped[str] = mapped_column(String(20))
    has_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_masked: Mapped[Optional[str]]
    embedding: Mapped[Optional[list]] = mapped_column(ARRAY(Float), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class JobContact(Base):
    __tablename__ = "job_contact"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    posting_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    phone_encrypted: Mapped[str]
    phone_type: Mapped[str] = mapped_column(String(20))
    department: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
