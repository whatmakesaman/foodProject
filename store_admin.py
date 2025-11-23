from flask import Flask, request, jsonify
import pymysql


app = Flask(__name__)
app.json.ensure_ascii = False  # 한글 깨짐 방지

def get_conn():
    """MySQL 연결을 생성합니다."""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="fooddb",
        db="fooddb",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
# =========================================================
# [관리자] 매장 정보 조회 (수정 페이지 진입용)
#  GET /api/stores/<store_id>
# =========================================================
@app.route("/api/stores/<int:store_id>", methods=["GET"])
def get_store(store_id):
    """
    매장 정보 수정 페이지에 들어갈 때,
    선택한 매장의 현재 정보를 조회하여 반환합니다.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    store_id,
                    name,
                    address,
                    `open`,
                    `close`,
                    phone,
                    distance
                FROM store
                WHERE store_id = %s
            """
            cur.execute(sql, (store_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "해당 매장을 찾을 수 없습니다."}), 404
    return jsonify(row), 200


# =========================================================
# [관리자] 매장 정보 수정
#  PUT /api/stores/<store_id>
# =========================================================
@app.route("/api/stores/<int:store_id>", methods=["PUT"])
def update_store(store_id):
    """
    매장 정보 수정 페이지에서 입력값을 수정 후 저장할 때 호출되는 API.
    필수: name, address
    선택: open, close, phone, distance
    """
    data = request.json or {}

    name = data.get("name")
    address = data.get("address")
    open_time = data.get("open")
    close_time = data.get("close")
    phone = data.get("phone")
    distance = data.get("distance")

    # 필수 값 체크
    if not name or not address:
        return (
            jsonify({"error": "필수 항목(name, address)이 누락되었습니다."}),
            400,
        )
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 매장 존재 여부 확인
            cur.execute("SELECT store_id FROM store WHERE store_id = %s", (store_id,))
            if not cur.fetchone():
                return jsonify({"error": "해당 매장을 찾을 수 없습니다."}), 404

            # 업데이트할 필드 구성
            update_fields = ["name = %s", "address = %s"]
            params = [name, address]

            if open_time is not None:
                update_fields.append("`open` = %s")
                params.append(open_time)

            if close_time is not None:
                update_fields.append("`close` = %s")
                params.append(close_time)

            if phone is not None:
                update_fields.append("phone = %s")
                params.append(phone)
            if distance is not None:
                update_fields.append("distance = %s")
                params.append(distance)

            params.append(store_id)

            sql = f"""
                UPDATE store
                SET {", ".join(update_fields)}
                WHERE store_id = %s
            """
            cur.execute(sql, params)
            conn.commit()

            # 수정된 내용 다시 조회해서 응답
            cur.execute(
                """
                SELECT
                    store_id,
                    name,
                    address,
                    `open`,
                    `close`,
                    phone,
                    distance
                FROM store
                WHERE store_id = %s
                """,
                (store_id,),
            )
            updated = cur.fetchone()
    finally:
        conn.close()

    return jsonify({"message": "매장 정보가 수정되었습니다.", "store": updated}), 200


# =========================================================
# [관리자] 매장 삭제
#  DELETE /api/stores/<store_id>
# =========================================================
@app.route("/api/stores/<int:store_id>", methods=["DELETE"])
def delete_store(store_id):
    """
    매장 정보 수정 페이지에서 삭제 버튼을 눌렀을 때,
    해당 매장을 데이터베이스에서 제거합니다.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 매장 존재 여부 확인
            cur.execute("SELECT store_id FROM store WHERE store_id = %s", (store_id,))
            if not cur.fetchone():
                return jsonify({"error": "해당 매장을 찾을 수 없습니다."}), 404

            # 매장 삭제
            cur.execute("DELETE FROM store WHERE store_id = %s", (store_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "매장이 삭제되었습니다."}), 200
if __name__ == "__main__":
    # 관리자용 매장 관리 서버 (포트 5000)
    # *기존 inquiry.py와 동시에 실행 시 포트 충돌이 날 수 있으므로, 동시 실행 시에는
    #  한쪽 포트를 변경하거나 각각 다른 터미널에서 순차 실행하세요.
    app.run(debug=True, port=5000)

