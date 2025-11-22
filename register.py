"""
----------------------------------------
이 파일은 Flask 기반 회원가입 처리 서버입니다.
사용자 유형(학생 / 사장)에 따라
student 혹은 provider 테이블에 먼저 데이터를 넣고,
user 테이블에 공통 정보(login_id, pw, name)를 저장합니다.
----------------------------------------
"""

from flask import Flask, render_template, request
from db import get_connection

app = Flask(__name__)

@app.route('/')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    login_id = request.form['login_id']
    pw = request.form['pw']
    name = request.form['name']
    user_type = request.form['type']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ------------------------------------
        # 1. 사장 가입
        # ------------------------------------
        if user_type == "provider":
            store_name = request.form['store_name']
            business_number = request.form['business_number']

            # provider insert
            cursor.execute("""
                INSERT INTO provider (store_name, pw, business_number, status, login_id)
                VALUES (%s, %s, %s, 'active', %s)
            """, (store_name, pw, business_number, login_id))

            # user insert (pro_id = provider 마지막 입력된 pro_id)
            cursor.execute("""
                INSERT INTO user (login_id, pw, name, pro_id)
                VALUES (%s, %s, %s, LAST_INSERT_ID())
            """, (login_id, pw, name))

        # ------------------------------------
        # 2. 학생 가입
        # ------------------------------------
        elif user_type == "student":
            school = request.form['school']
            student_id = request.form['student_id']

            # student insert
            cursor.execute("""
                INSERT INTO student (student_id, major)
                VALUES (%s, %s)
            """, (student_id, school))

            # user insert (student_id 연결)
            cursor.execute("""
                INSERT INTO user (login_id, pw, name, student_id)
                VALUES (%s, %s, %s, %s)
            """, (login_id, pw, name, student_id))

        conn.commit()
        return "<h2>회원가입 성공!</h2>"

    except Exception as e:
        conn.rollback()
        return f"<h2>회원가입 실패:<br>{e}</h2>"

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)