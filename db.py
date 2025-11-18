"""
이 파일은 MySQL 데이터베이스(fooddb)에 연결을 생성하는 역할만 담당합니다.

다른 Python 파일(서버, 라우터, 기능 코드 등)에서
데이터베이스가 필요할 때, get_connection() 함수를 호출하여
공통된 DB 연결 방식을 사용할 수 있도록 분리해둔 파일입니다.
"""

import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root', 
        db='fooddb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )