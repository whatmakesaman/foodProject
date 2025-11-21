from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from ranking import get_rank
import decimal
from db import get_connection
from datetime import datetime



app = Flask(__name__)
CORS(app)   # 프론트와 포트 달라도 요청 가능하게

def convert_decimal(rows):
    """Decimal 타입을 float으로 변환 (JSON 응답용)"""
    converted = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, decimal.Decimal):
                new_row[k] = float(v)
            else:
                new_row[k] = v
        converted.append(new_row)
    return converted

@app.route("/api/rank", methods=["GET"])
def api_rank():
    # 쿼리스트링에서 값 받기
    limit = int(request.args.get("limit", 10))
    offset = int(request.args.get("offset", 0))
    min_reviews = int(request.args.get("min_reviews", 0))
    use_adv = request.args.get("use_adv", "1") == "1"  # "1"이면 True

    rows = get_rank(limit=limit,
                    offset=offset,
                    min_reviews=min_reviews,
                    use_adv=use_adv)

    rows = convert_decimal(rows)
    return jsonify(rows)

@app.route("/api/inquiries", methods=["POST", "OPTIONS"])
def create_inquiry():
    # preflight(OPTIONS) 요청 오면 여기서 바로 통과시켜 주기
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()

    user_id = data.get("user_id")
    title = data.get("title")
    writer = data.get("writer")
    field = data.get("field")
    content = data.get("content")

    if not user_id or not title or not content:
        return jsonify({"error": "user_id, title, content는 필수입니다."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO inquiry (user_id, title, writer, field, content)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(sql, (user_id, title, writer, field, content))
            conn.commit()
            inquiry_id = cur.lastrowid
    finally:
        conn.close()

    return jsonify({"inquiry_id": inquiry_id}), 201

@app.route("/api/inquiries", methods=["GET"])
def list_inquiries():
    # 쿼리스트링에서 user_id 받기 (없으면 None)
    user_id = request.args.get("user_id", type=int)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    inquiry_id,
                    user_id,
                    title,
                    writer,
                    field,
                    content,
                    answer,
                    created_at
                FROM inquiry
            """
            params = []
            if user_id is not None:
                sql += " WHERE user_id = %s"
                params.append(user_id)

            sql += " ORDER BY inquiry_id DESC"

            cur.execute(sql, params)
            rows = cur.fetchall()

            # datetime → 문자열로 변환
            for r in rows:
                if isinstance(r.get("created_at"), datetime):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    finally:
        conn.close()

    return jsonify(rows)

#랭킹페이지 출력
@app.route('/ranking')
def ranking_page():
    """랭킹 페이지"""
    return render_template('ranking.html')


# ⚠️ 모든 라우트 정의가 끝난 뒤에!
if __name__ == "__main__":
    app.run(debug=True)
