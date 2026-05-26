"""
1회성 배치 스크립트: job_posting 전체 임베딩 계산 후 DB 저장

실행 방법 (EC2에서):
    docker exec gowork-app python scripts/compute_embeddings.py

소요 시간: 약 3~5분 (56,628건 기준)
"""

import logging
import time

import psycopg2
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = None  # 환경변수에서 자동 로드

BATCH_SIZE = 256


def get_conn():
    import os

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    return psycopg2.connect(url)


def main():
    logger.info("임베딩 모델 로딩 중...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    conn = get_conn()
    cur = conn.cursor()

    # embedding 컬럼이 없으면 추가
    cur.execute("""
        ALTER TABLE job_posting
        ADD COLUMN IF NOT EXISTS embedding FLOAT4[]
    """)
    conn.commit()
    logger.info("embedding 컬럼 준비 완료")

    # 임베딩 없는 공고 조회
    cur.execute("""
        SELECT id, COALESCE(title_raw, '') as text
        FROM job_posting
        WHERE embedding IS NULL
        ORDER BY collected_at DESC
    """)
    rows = cur.fetchall()
    total = len(rows)
    logger.info(f"임베딩 계산 대상: {total}건")

    t_start = time.perf_counter()
    processed = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = rows[batch_start : batch_start + BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        vecs = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False)

        cur.executemany(
            "UPDATE job_posting SET embedding = %s WHERE id = %s",
            [(vec.tolist(), id_) for vec, id_ in zip(vecs, ids)],
        )
        conn.commit()

        processed += len(batch)
        elapsed = time.perf_counter() - t_start
        rate = processed / elapsed
        remaining = (total - processed) / rate if rate > 0 else 0
        logger.info(
            f"진행: {processed}/{total}건 "
            f"({processed/total*100:.1f}%) "
            f"| 예상 남은 시간: {remaining:.0f}s"
        )

    logger.info(f"완료! 총 소요: {time.perf_counter()-t_start:.1f}s")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
