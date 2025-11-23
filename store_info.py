"""
store_info.py
----------------------------------------
매장 상세 정보 조회 API
- GET /api/stores/<store_id>/detail : 매장 상세 정보 조회
"""

from flask import Blueprint, jsonify
from db import get_connection
from datetime import datetime, timedelta
import decimal

bp = Blueprint('store_info', __name__)


@bp.route("/api/stores/<int:store_id>/detail", methods=["GET"])
def get_store_detail(store_id):
    """
    매장 상세 정보 조회 API
    - 매장 기본 정보
    - 통계 정보 (평균 평점, 리뷰 수, 베이지안 점수)
    - 메뉴 목록
    - 최근 리뷰 목록
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 1. 매장 기본 정보 조회
            cur.execute("""
                SELECT 
                    store_id,
                    name,
                    address,
                    open_time,
                    close_time,
                    phone,
                    distance_km,
                    category_id
                FROM store
                WHERE store_id = %s
            """, (store_id,))
            store_info = cur.fetchone()
            
            if not store_info:
                return jsonify({"error": "해당 매장을 찾을 수 없습니다."}), 404
            
            # 2. 통계 정보 조회 (랭킹 뷰에서) - 뷰가 없을 수 있으므로 예외 처리
            stats = None
            try:
                cur.execute("""
                    SELECT 
                        avg_rating,
                        review_cnt,
                        bayes_score
                    FROM v_store_ranking
                    WHERE store_id = %s
                """, (store_id,))
                stats = cur.fetchone()
            except Exception as e:
                print(f"통계 정보 조회 오류 (뷰가 없을 수 있음): {e}")
                stats = None
            
            # 3. 메뉴 목록 조회
            cur.execute("""
                SELECT 
                    menu_id,
                    name,
                    price,
                    recommend
                FROM menu
                WHERE store_id = %s
                ORDER BY menu_id
            """, (store_id,))
            menus = cur.fetchall()
            
            # 4. 최근 리뷰 목록 조회 (최대 10개)
            cur.execute("""
                SELECT 
                    review_id,
                    user_id,
                    content,
                    rating,
                    helpful_cnt,
                    created_at
                FROM review
                WHERE store_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (store_id,))
            reviews = cur.fetchall()
            
            # datetime → 문자열로 변환
            for review in reviews:
                if isinstance(review.get("created_at"), datetime):
                    review["created_at"] = review["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            
            # open_time, close_time이 timedelta인 경우 문자열로 변환
            if isinstance(store_info.get("open_time"), timedelta):
                total_seconds = store_info["open_time"].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                store_info["open_time"] = f"{hours:02d}:{minutes:02d}"
            
            if isinstance(store_info.get("close_time"), timedelta):
                total_seconds = store_info["close_time"].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                store_info["close_time"] = f"{hours:02d}:{minutes:02d}"
            
            # Decimal 타입 변환
            if store_info.get("distance_km"):
                store_info["distance_km"] = float(store_info["distance_km"])
            
            if stats:
                if stats.get("avg_rating"):
                    stats["avg_rating"] = float(stats["avg_rating"])
                if stats.get("bayes_score"):
                    stats["bayes_score"] = float(stats["bayes_score"])
            
            # 응답 데이터 구성
            result = {
                "store": store_info,
                "stats": stats or {
                    "avg_rating": 0,
                    "review_cnt": 0,
                    "bayes_score": 0
                },
                "menus": menus,
                "reviews": reviews
            }
            
            return jsonify(result), 200
            
    except Exception as e:
        print(f"매장 정보 조회 오류: {e}")
        return jsonify({"error": "매장 정보를 불러오는 중 오류가 발생했습니다."}), 500
    finally:
        if conn:
            conn.close()
