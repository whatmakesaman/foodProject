"""
login.py
----------------------------------------
로그인 기능 전체 처리:
- /              : 사용자/관리자 탭 UI (login_tab.html)
- /login         : 학생/사장 로그인 처리
- /admin_login   : 관리자 로그인 처리
----------------------------------------
"""

from flask import Flask, render_template, request
from db import get_connection

app = Flask(__name__)


# ==========================
# 0. 탭 UI 메인 화면
# ==========================
@app.route('/')
def login_tab():
    return render_template('login_tab.html')


# ==========================
# 1. 학생/사장 로그인
# ==========================
@app.route('/login')
def login_page():
    return render_template('login.html')  # 혹시 직접 접근할 경우용


@app.route('/login', methods=['POST'])
def login():
    login_id = request.form['login_id']
    pw = request.form['pw']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM user WHERE login_id=%s AND pw=%s
    """, (login_id, pw))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return "<h2>로그인 실패: 아이디 또는 비밀번호 오류</h2>"

    # 🔥 사용자 탭에서 관리자 계정 로그인 시 차단
    if user['student_id'] is None and user['pro_id'] is None:
        return "<h2>사용자 로그인 실패: 관리자는 사용자 탭에서 로그인할 수 없습니다.</h2>"

    # 학생 로그인
    if user['student_id'] is not None:
        return f"<h2>학생 로그인 성공!<br>{user['name']}님 환영합니다.</h2>"

    # 사장 로그인
    if user['pro_id'] is not None:
        return f"<h2>사장 로그인 성공!<br>{user['name']}님 환영합니다.</h2>"

    return "<h2>로그인 실패: 계정 유형 오류</h2>"


# ==========================
# 2. 관리자 로그인
# ==========================
@app.route('/admin_login')
def admin_login_page():
    return render_template('admin_login.html')  # 혹시 직접 접근할 경우용


@app.route('/admin_login', methods=['POST'])
def admin_login():
    login_id = request.form['login_id']
    pw = request.form['pw']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM site_admin WHERE login_id=%s AND pw=%s
    """, (login_id, pw))

    admin = cursor.fetchone()
    conn.close()

    if admin:
        return f"<h2>관리자 로그인 성공!<br>{admin['admin_name']}님 환영합니다.</h2>"
    else:
        return "<h2>관리자 로그인 실패: 관리자 계정이 아닙니다.</h2>"


if __name__ == '__main__':
    app.run(port=5001, debug=True)