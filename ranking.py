import sys, io
import pymysql
from db import get_connection   # ✅ db.py에서 연결 함수 가져오기

# (옵션) 콘솔 한글 깨짐 방지 – 터미널 테스트용
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def get_rank(limit=10, offset=0, min_reviews=0, use_adv=True):
    """
    - use_adv=True  : v_store_ranking.bayes_score 사용
    - use_adv=False : v_store_ranking.avg_rating 사용(간단 점수)
    """
    score_expr = "bayes_score" if use_adv else "avg_rating"

    sql = f"""
        SELECT
            store_id,
            name,
            distance_km,
            review_cnt,
            avg_rating,
            {score_expr} AS score
        FROM v_store_ranking
        WHERE review_cnt >= %s
        ORDER BY score DESC, review_cnt DESC
        LIMIT %s OFFSET %s
    """

    params = [min_reviews, limit, offset]

    conn = get_connection()   # ✅ 여기서 DB 연결 생성
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()          # ✅ 사용 후 연결 닫기

    return rows


# 터미널에서 단독 실행 테스트용
if __name__ == "__main__":
    rows = get_rank(limit=10, min_reviews=0, use_adv=True)
    for r in rows:
        print(f"{r['name']} | 점수 {float(r['score']):.3f} | "
              f"평점 {float(r['avg_rating']):.2f} | 리뷰 {r['review_cnt']} | 거리 {r['distance_km']}")
