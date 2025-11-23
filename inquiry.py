# inquiry.py

from flask import Flask, request, jsonify, render_template
import pymysql



app = Flask(__name__)
app.json.ensure_ascii = False

def get_conn():
    return pymysql.connect(
        host='localhost',
        user='food',
        password='root',  
        db='fooddb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
# 로그인 붙으면 여기서 세션에서 user_id, role 꺼내면 됨
def get_current_user():
    # 나중에는 세션, DB에서 가져옴
    return {
        "user_id": 1,
        "role": "user"   # 또는 "admin"
    }

# 로그인 붙으면 여기서 세션에서 user_id 꺼내면 됨
def get_current_user_id():
    return get_current_user()["user_id"]  # 테스트용. 나중에 진짜 로그인 연동

@app.route("/inquiry", methods=["GET"])
def inquiry_page():
    return render_template("inquiry.html")


#사용자가 문의
@app.route('/api/inquiries', methods=['POST'])
def create_inquiry():
      
    data = request.json  # JSON으로 받는다고 가정

    user_id = data.get('user_id')      # 나중엔 get_current_user_id()로 대체
    title = data.get('title')
    writer = data.get('writer')
    content = data.get('content')
    field = data.get('field')

    if not user_id or not title or not content:
        return jsonify({'error': 'user_id, title, content는 필수입니다.'}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO inquiry (user_id, title, writer, content, field)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(sql, (user_id, title, writer, content, field))
            conn.commit()
            inquiry_id = cur.lastrowid
    finally:
        conn.close()

    
    return jsonify({
        'message': '문의가 등록되었습니다.',
        'inquiry_id': inquiry_id
    }), 201

#사용자가 자신의 문의 확인

@app.route('/api/inquiries/me', methods=['GET'])
def list_my_inquiries_api():
    user_id = get_current_user_id()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT inquiry_id, title, field, created_at, answer
                FROM inquiry
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200
@app.route('/my/inquiries', methods=['GET'])
def my_inquiries_page():
    user_id = get_current_user_id()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT inquiry_id, title, field, created_at, answer
                FROM inquiry
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            inquiries = cur.fetchall()
    finally:
        conn.close()

    return render_template("my_inquiry_list.html", inquiries=inquiries)



# 사용자의 문의 상세/답변 보기
@app.route("/my/inquiries/<int:inquiry_id>", methods=["GET"])
def my_inquiry_detail_page(inquiry_id):
    user_id = get_current_user_id()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT inquiry_id, user_id, title, writer, field,
                       content, created_at, answer
                FROM inquiry
                WHERE inquiry_id = %s AND user_id = %s
            """
            cur.execute(sql, (inquiry_id, user_id))
            inquiry = cur.fetchone()
    finally:
        conn.close()

    if not inquiry:
        return "해당 문의를 찾을 수 없습니다.", 404

    return render_template("my_inquiry_detail.html", inquiry=inquiry)

#관리자 답변 등록/수정
@app.route('/api/admin/inquiries/<int:inquiry_id>/answer', methods=['POST'])
def set_inquiry_answer(inquiry_id):
    data = request.json
    answer = data.get('answer')

    if answer is None:
        return jsonify({'error': 'answer 내용이 비어 있습니다.'}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                UPDATE inquiry
                SET answer = %s
                WHERE inquiry_id = %s
            """
            cur.execute(sql, (answer, inquiry_id))
            conn.commit()

            if cur.rowcount == 0:
                return jsonify({'error': '해당 문의가 존재하지 않습니다.'}), 404
    finally:
        conn.close()

    return jsonify({'message': '답변이 저장되었습니다.'}), 200
#문의 상세+답변조회
@app.route('/api/inquiries/<int:inquiry_id>', methods=['GET'])
def get_inquiry_detail(inquiry_id):
    user_id = get_current_user_id()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT inquiry_id, user_id, title, writer, field,
                       content, created_at, answer
                FROM inquiry
                WHERE inquiry_id = %s AND user_id = %s
            """
            cur.execute(sql, (inquiry_id, user_id))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({'error': '해당 문의를 찾을 수 없습니다.'}), 404

    return jsonify(row), 200

#관리자용 문의 목록
@app.route("/admin/inquiries")
def admin_inquiry_list():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT inquiry_id, title, writer, field, created_at, answer
                FROM inquiry
                ORDER BY created_at DESC
            """
            cur.execute(sql)
            inquiries = cur.fetchall()
    finally:
        conn.close()

    # inquiries: [{ 'inquiry_id': 1, 'title': ..., ... }, ...]
    return render_template("admin_inquiry_list.html", inquiries=inquiries)

#관리자용 문의 상세 + 답변
from flask import redirect, url_for

@app.route("/admin/inquiries/<int:inquiry_id>", methods=["GET", "POST"])
def admin_inquiry_detail(inquiry_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                # form에서 넘어온 answer 저장
                answer = request.form.get("answer")

                update_sql = """
                    UPDATE inquiry
                    SET answer = %s
                    WHERE inquiry_id = %s
                """
                cur.execute(update_sql, (answer, inquiry_id))
                conn.commit()

                # 저장 후 다시 상세 페이지로 이동
                return redirect(url_for("admin_inquiry_detail", inquiry_id=inquiry_id))

            # GET 요청일 때는 문의 내용 조회
            select_sql = """
                SELECT inquiry_id, user_id, title, writer, field, content, created_at, answer
                FROM inquiry
                WHERE inquiry_id = %s
            """
            cur.execute(select_sql, (inquiry_id,))
            inquiry = cur.fetchone()
    finally:
        conn.close()

    if not inquiry:
        return "해당 문의를 찾을 수 없습니다.", 404

    return render_template("admin_inquiry_detail.html", inquiry=inquiry)


if __name__ == '__main__':
    app.run(debug=True)
