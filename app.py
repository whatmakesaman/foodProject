from flask import Flask, jsonify, request, send_from_directory, g, render_template, redirect

from flask_cors import CORS
from ranking import get_rank
import decimal
from db import get_connection
from datetime import datetime, timedelta
import pymysql
import jwt
from functools import wraps

# store_info Blueprint import
from store_info import bp as store_info_bp


# ======================
# Flask 기본 설정
# ======================
# 기존에 사용하던 static 설정 그대로 유지
app = Flask(__name__)
CORS(app)  # 프론트와 포트 달라도 요청 가능하게

app.config['SECRET_KEY'] = 'login'  # 나중에 더 복잡한 문자열로 바꿔도 됨

# Blueprint 등록 (store_info)
app.register_blueprint(store_info_bp)


# ======================
# JWT 토큰 생성 (일반 사용자용)
# ======================
def create_token(user_id, name, role=None):
    payload = {
        'user_id': user_id,
        'name': name,
        'role': role,  # student / provider / admin 등
        'exp': datetime.utcnow() + timedelta(hours=6)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    # PyJWT 버전에 따라 bytes 로 나올 수도 있어서 처리
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


# ======================
# 공통 함수
# ======================
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

# ======================
# 랭킹 API
# GET /api/rank
# ======================
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
# ======================
# JWT 데코레이터들
# ======================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # CORS preflight(OPTIONS)는 토큰 검사 없이 통과
        if request.method == "OPTIONS":
            return "", 200

        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "인증 토큰이 필요합니다."}), 401

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(
                token, app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "토큰이 만료되었습니다."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "유효하지 않은 토큰입니다."}), 401

        user_id = payload.get("user_id")
        name = payload.get("name")
        role = payload.get("role")

        # 관리자 토큰(site_admin용) 같은 건 여기서 막아버림
        if user_id is None or name is None:
            return jsonify({"message": "유효하지 않은 사용자 토큰입니다."}), 401

        g.user_id = user_id
        g.user_name = name
        g.role = role

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # PUT 요청 CORS preflight(OPTIONS) 통과
        if request.method == "OPTIONS":
            return "", 200

        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': '인증 토큰이 필요합니다.'}), 401

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '토큰이 만료되었습니다.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '유효하지 않은 토큰입니다.'}), 401

        if payload.get('role') != 'admin':
            return jsonify({'message': '관리자 권한이 필요합니다.'}), 403

        g.admin_id = payload.get('admin_id')
        g.admin_name = payload.get('admin_name')

        return f(*args, **kwargs)
    return decorated


# ======================
# 일반 사용자 로그인
# POST /api/login
# (user 테이블 기준)
# ======================
@app.route("/api/login", methods=["POST"])
def user_login():
    data = request.get_json() or {}
    login_id = data.get("login_id")
    password = data.get("password") or data.get("pw")

    if not login_id or not password:
        return jsonify({"message": "아이디와 비밀번호를 입력하세요."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT user_id, login_id, pw, name
                FROM user
                WHERE login_id = %s
            """
            cursor.execute(sql, (login_id,))
            user = cursor.fetchone()
    finally:
        conn.close()

    # 아이디 / 비밀번호 검증
    if not user or user["pw"] != password:
        return jsonify({"message": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

    # 토큰 생성
    token = create_token(user["user_id"], user["name"], role=None)

    # 토큰 + 유저 정보 같이 응답
    return jsonify({
        "message": "로그인 성공",
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "login_id": user["login_id"],
            "name": user["name"]
        }
    }), 200


# ======================
# 문의 등록
# POST /api/inquiries
# ======================
@app.route("/api/inquiries", methods=["POST", "OPTIONS"])
@login_required
def create_inquiry():
    # preflight(OPTIONS) 요청 오면 바로 통과
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}

    user_id = g.user_id
    writer = g.user_name   # 프론트에서 writer 안 받아도 됨
    title = data.get("title")
    field = data.get("field")
    content = data.get("content")

    if not title or not content:
        return jsonify({"error": "title, content는 필수입니다."}), 400
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


# ======================
# 문의 목록 (로그인한 사용자)
# GET /api/inquiries
# ======================
@app.route("/api/inquiries", methods=["GET"])
@login_required
def list_inquiries():
    # 쿼리 파라미터에 user_id를 넘겨도 되지만,
    # 기본은 "내 문의 목록"이 되도록 토큰의 user_id 사용
    user_id_param = request.args.get("user_id", type=int)
    user_id = user_id_param if user_id_param is not None else g.user_id

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
                WHERE user_id = %s
                ORDER BY inquiry_id DESC
            """
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()

            # datetime → 문자열로 변환
            for r in rows:
                if isinstance(r.get("created_at"), datetime):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    finally:
        conn.close()

    return jsonify(rows)

# ======================
# 문의 상세 (사용자 본인 것만)
# GET /api/inquiries/<id>
# ======================
@app.route('/api/inquiries/<int:inquiry_id>', methods=['GET'])
@login_required
def get_inquiry_detail(inquiry_id):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT inquiry_id, user_id, title, writer, created_at, content, answer, field
        FROM inquiry
        WHERE inquiry_id = %s
    """
    cursor.execute(sql, (inquiry_id,))
    inquiry = cursor.fetchone()

    cursor.close()
    conn.close()

    if not inquiry:
        return jsonify({"error": "문의가 존재하지 않습니다."}), 404

    # 내 문의가 아니면 막기
    if inquiry['user_id'] != g.user_id:
        return jsonify({"error": "해당 문의에 접근할 권한이 없습니다."}), 403

    # created_at 포맷 변환
    if isinstance(inquiry.get("created_at"), datetime):
        inquiry["created_at"] = inquiry["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(inquiry)
# 문의 상세 페이지 (HTML) → 데코레이터 제거!
@app.route('/inquiry_detail', methods=['GET'])
def inquiry_detail_page():
    inquiry_id = request.args.get('id', type=int)
    if inquiry_id is None:
        # id 없으면 목록으로 돌려보내도 되고, 에러 띄워도 됨
        return redirect('/my_inquiry_list')

    return render_template('inquiry_detail.html', inquiry_id=inquiry_id)



# ======================
# 문의 답변 수정 (관리자용으로 쓸 예정)
# PUT /api/inquiries/<id>/answer
# ======================
@app.route('/api/inquiries/<int:inquiry_id>/answer', methods=['PUT', 'OPTIONS'])
@admin_required
def update_inquiry_answer(inquiry_id):
    # preflight(OPTIONS) 통과
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}
    answer = data.get('answer')

    if not answer or answer.strip() == "":
        return jsonify({"error": "answer 값이 비어 있습니다."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    sql = "UPDATE inquiry SET answer = %s WHERE inquiry_id = %s"
    cursor.execute(sql, (answer, inquiry_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"result": "ok", "inquiry_id": inquiry_id, "answer": answer})


# ======================
# 모든 문의(관리자 전체 조회용)
# GET /api/inquiries_all
# ======================
@app.route('/api/inquiries_all', methods=['GET'])
def get_all_inquiries():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    inquiry_id,
                    user_id,
                    title,
                    writer,
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') AS created_at,
                    content,
                    answer,
                    field
                FROM inquiry
                ORDER BY inquiry_id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
        return jsonify(rows), 200
    finally:
        conn.close()


# ======================
# 로그인 화면
# ======================
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# ======================
# 랭킹 / 매장 상세 페이지
# ======================
@app.route('/ranking')
def ranking_page():
    return render_template('ranking.html')


@app.route('/ranking/store_info/<int:store_id>')
def store_detail_page(store_id):
    return render_template('store_detail.html', store_id=store_id)


# ======================
# 회원가입 페이지 + 회원가입 처리
# ======================
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.get_json() or {}

    login_id = data.get('login_id')
    password = data.get('password') or data.get('pw')
    name = data.get('name')

    user_type = data.get('userType')
    student_id = data.get('student_id')
    pro_id = data.get('pro_id')

    if not login_id or not password or not name:
        return jsonify({"message": "아이디, 비밀번호, 이름은 필수입니다."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM user WHERE login_id = %s",
                (login_id,)
            )
            exist = cur.fetchone()
            if exist:
                return jsonify({"message": "이미 존재하는 아이디입니다."}), 409

            sql = """
                INSERT INTO user (login_id, pw, name, create_at)
                VALUES (%s, %s, %s, NOW())
            """
            cur.execute(sql, (login_id, password, name))
            conn.commit()
            user_id = cur.lastrowid
    finally:
        conn.close()

    return jsonify({
        "message": "회원가입 성공",
        "user": {
            "user_id": user_id,
            "login_id": login_id,
            "name": name
        }
    }), 201


# ======================
# 문의 페이지 화면 라우트
# ======================
@app.route('/inquiry', methods=['GET'])
def inquiry_page():
    return render_template('inquiry.html')


@app.route('/my_inquiry_list', methods=['GET'])
def my_inquiry_list():
    return render_template('my_inquiry_list.html')


# ======================
# 매장 검색
# ======================
@app.route('/api/stores/search', methods=['GET'])
def search_store():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': '검색어가 없습니다.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT store_id, name
                FROM store
                WHERE name LIKE %s
                ORDER BY name
            """
            cur.execute(sql, (f"%{q}%",))
            stores = cur.fetchall()
    finally:
        conn.close()

    if not stores:
        return jsonify({'error': '매장을 찾을 수 없습니다.'}), 404

    return jsonify(stores)


@app.route('/admin/store/search', methods=['GET'])
def admin_store_search_page():
    """매장 검색 페이지를 보여줍니다."""
    return render_template('store_search.html')

@app.route('/admin/store/<int:store_id>', methods=['GET'])
def admin_store_edit(store_id):
    return render_template('store_admin_edit.html', store_id=store_id)

# ======================
# 관리자 로그인 페이지 라우트
# ======================
@app.route('/admin_login', methods=['GET'])
def admin_login_page():
    return render_template('admin_login.html')

# ======================
# 관리자 로그인
# POST /api/admin/login
# ======================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    login_id = data.get('login_id')
    password = data.get('password')

    if not login_id or not password:
        return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력하세요.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT admin_id, login_id, admin_name
                FROM site_admin
                WHERE login_id = %s AND pw = %s
            """
            cursor.execute(sql, (login_id, password))
            admin = cursor.fetchone()
    finally:
        conn.close()

    if not admin:
        return jsonify({'success': False, 'message': '관리자 계정이 아니거나 비밀번호가 올바르지 않습니다.'}), 401

    return jsonify({
        'success': True,
        'admin': {
            'admin_id': admin['admin_id'],
            'admin_name': admin['admin_name']
        }
    }), 200

# 관리자 문의 목록 페이지
@app.route('/admin_inquiry_list', methods=['GET'])
def admin_inquiry_list_page():
    return render_template('admin_inquiry_list.html')


# 관리자 문의 상세 + 답변 작성 페이지
@app.route('/admin_inquiry_detail', methods=['GET'])
def admin_inquiry_detail_page():
    inquiry_id = request.args.get('id', type=int)
    return render_template('admin_inquiry_detail.html', inquiry_id=inquiry_id)

# -------------------------------------------
# 관리자 전용: 문의 상세 조회
# GET /api/admin/inquiries/<inquiry_id>
# -------------------------------------------
@app.route('/api/admin/inquiries/<int:inquiry_id>', methods=['GET'])
def admin_get_inquiry(inquiry_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    inquiry_id,
                    user_id,
                    title,
                    writer,
                   DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') AS created_at,
                    content,
                    answer,
                    field
                FROM inquiry
                WHERE inquiry_id = %s
            """
            cursor.execute(sql, (inquiry_id,))
            row = cursor.fetchone()

        if not row:
            return jsonify({'error': '해당 문의를 찾을 수 없습니다.'}), 404

        return jsonify(row), 200
    finally:
        conn.close()


# -------------------------------------------
# 관리자 전용: 답변 저장 / 수정
# PUT /api/admin/inquiries/<inquiry_id>/answer
# -------------------------------------------
@app.route('/api/admin/inquiries/<int:inquiry_id>/answer', methods=['PUT'])
def admin_update_inquiry_answer(inquiry_id):
    data = request.get_json()
    answer = (data.get('answer') or '').strip()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE inquiry SET answer = %s WHERE inquiry_id = %s"
            cursor.execute(sql, (answer, inquiry_id))
        conn.commit()
        return jsonify({'message': '답변이 저장되었습니다.'}), 200
    finally:
        conn.close()

@app.route('/api/admin/menu/<int:menu_id>', methods=['PUT'])
def admin_update_menu(menu_id):
    data = request.get_json() or {}

    new_name = data.get('name')
    new_price = data.get('price')

    if not new_name:
        return jsonify({'message': '메뉴 이름은 필수입니다.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                UPDATE menu
                SET name = %s,
                    price = %s
                WHERE menu_id = %s
            """
            cur.execute(sql, (new_name, new_price, menu_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'message': '메뉴가 수정되었습니다.'}), 200

@app.route('/api/admin/menu/<int:menu_id>', methods=['DELETE'])
def admin_delete_menu(menu_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 메뉴 존재 여부 확인
            cur.execute("SELECT menu_id FROM menu WHERE menu_id = %s", (menu_id,))
            if not cur.fetchone():
                return jsonify({'message': '해당 메뉴를 찾을 수 없습니다.'}), 404
            
            # 메뉴 삭제
            cur.execute("DELETE FROM menu WHERE menu_id = %s", (menu_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'message': '메뉴가 삭제되었습니다.'}), 200

# ======================
# 실행
# ======================
if __name__ == "__main__":
    app.run(debug=True)
