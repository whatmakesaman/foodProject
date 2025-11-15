import pymysql
import sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


conn = pymysql.connect(
    host='localhost',
    user='root',
    password='fooddb',   # 실제 root 비번으로 맞추세요
    db='fooddb',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def get_rank(limit=10, offset=0, min_reviews=0, use_adv=True):
    """
    - use_adv=True  : v_store_ranking의 bayes_score 사용
    - use_adv=False : v_store_ranking의 avg_rating 사용(간단 점수)
    """
    # v_store_ranking에 컬럼: store_id, name, address, distance_km, avg_rating, review_cnt, bayes_score ...
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

    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

if __name__ == "__main__":
    rows = get_rank(limit=10, min_reviews=0, use_adv=True)
    for r in rows:
        print(f"{r['name']} | 점수 {float(r['score']):.3f} | 평점 {float(r['avg_rating']):.2f} | 리뷰 {r['review_cnt']} | 거리 {r['distance_km']}")
