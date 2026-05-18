import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///jobs.db")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    TOKEN_EXPIRE_HOURS: int = 24 * 7  # 7일

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # 모델 설정 (Groq)
    MAIN_MODEL: str = "llama-3.3-70b-versatile"  # 최종 응답용 (고품질)
    FAST_MODEL: str = "llama-3.1-8b-instant"  # 분류/추출용 (빠름)

    # 온도 설정
    MAIN_TEMPERATURE: float = 0.7
    FAST_TEMPERATURE: float = 0.0  # 분류/추출은 결정론적으로

    # 메모리
    MAX_HISTORY_TURNS: int = 10  # 최근 N턴 대화만 유지 (5턴이면 구인구직 흐름상 충분)

    # 검색
    MAX_JOB_RESULTS: int = 5  # 한 번에 추천할 최대 일자리 수

    # 디버깅
    LOG_LLM: bool = True  # LLM 입출력 터미널 로그 (운영 시 False로 변경)


config = Config()
