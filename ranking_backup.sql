SET NAMES utf8mb4;

-- =========================================================
-- 스키마 생성 및 사용
-- =========================================================
DROP SCHEMA IF EXISTS `fooddb`;
CREATE SCHEMA IF NOT EXISTS `fooddb` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `fooddb`;

-- =========================================================
-- 최소 의존성 테이블: category, app_user
-- =========================================================
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `category_id` INT NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(30) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uq_category_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `category` (`name`)
VALUES ('한식'), ('중식'), ('양식'), ('일식'), ('분식'), ('카페'), ('디저트');

INSERT INTO category (category_id, name)
VALUES (1, '한식'),(2,'중식'),(3,'양식'),(4,'일식'),(5,'분식'),(6,'카페'),(7,'디저트');


DROP TABLE IF EXISTS `app_user`;
CREATE TABLE `app_user` (
  `user_id`    INT NOT NULL AUTO_INCREMENT COMMENT '사용자의 id',
  `name`       VARCHAR(30) NOT NULL,
  `pw`         VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  KEY `idx_user_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 테스트 사용자(선택)
INSERT INTO `app_user` (name, pw) VALUES ('준혁','1234'),('홍길동','abcd'),('김코딩','pass');

-- =========================================================
-- 핵심 1) store
-- =========================================================
DROP TABLE IF EXISTS `store`;
CREATE TABLE `store` (
  `store_id`     INT NOT NULL AUTO_INCREMENT COMMENT '매장의 id',
  `name`         VARCHAR(60) NOT NULL,
  `address`      VARCHAR(150),
  `open_time`    TIME,
  `close_time`   TIME,
  `phone`        VARCHAR(30),
  `distance_km`  DECIMAL(6,2),
  `category_id`  INT,
  PRIMARY KEY (`store_id`),
  KEY `idx_store_category` (`category_id`),
  CONSTRAINT `fk_store_category`
    FOREIGN KEY (`category_id`) REFERENCES `category`(`category_id`)
    ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 샘플 매장(선택)
INSERT INTO store (name, address, open_time, close_time, phone, distance_km, category_id)
VALUES ('금성이네', '경기 시흥시 정왕동 ', '16:00','01:00','010-9092-4992', 0.5, 1),
		( '쭈꾸미삼겹살', '경기 시흥시 정왕동 ', '11:00','01:00','050-4110-8859', 0.6, 1   ),
        ( '24시 수육국밥', '경기 시흥시 정왕동 ', '00:00','24:00','031-319-8676', 0.9, 1   ),
         ( '고향 칼국수', '경기 시흥시 정왕동 ', '11:00','20:00','031-499-7374', 1.0, 1   ),
           ( '국민 낙곱새', '경기 시흥시 정왕동 ', '14:00','03:00','031-433-9284', 1.0, 1   ),
           ( '더베이징', '경기 시흥시 정왕동 ', '11:00','21:30','031-319-4289', 0.2, 2   ),
            ( '라홍방 마라탕', '경기 시흥시 정왕동 ', '10:00','22:20','031-498-4776', 0.5, 2   ),
            ( '회전훠쿼핫', '경기 시흥시 정왕동 ', '11:00','22:20','0507-1349-3305', 0.7, 2   ),
             ( '짬뽕관', '경기 시흥시 정왕동 ', '10:30','21:30','010-9282-1633', 0.8, 2   ),
             ( '니뽕내뽕', '경기 시흥시 정왕동 ', '11:00','19:50','031-431-3564', 1.0, 2   )
             
           ;

-- =========================================================
-- 핵심 2) menu
-- =========================================================
DROP TABLE IF EXISTS `menu`;
CREATE TABLE `menu` (
  `menu_id`   INT NOT NULL AUTO_INCREMENT,
  `store_id`  INT NOT NULL COMMENT '매장의 id',
  `name`      VARCHAR(60) NOT NULL,
  `price`     INT NOT NULL,
  `recommend` VARCHAR(60),
  PRIMARY KEY (`menu_id`),
  UNIQUE KEY `uq_menu_store_name` (`store_id`, `name`),
  KEY `idx_menu_store` (`store_id`),
  CONSTRAINT `fk_menu_store`
    FOREIGN KEY (`store_id`) REFERENCES `store`(`store_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 샘플 메뉴(선택)
INSERT INTO menu (store_id, name, price) VALUES
-- 1. 금성이네 (한식)
(1, '김치찌개', 8000),
(1, '된장찌개', 8000),
(1, '삼겹살 1인분', 14000),

-- 2. 쭈꾸미삼겹살 (한식)
(2, '쭈꾸미볶음', 11000),
(2, '삼겹살추가', 7000),
(2, '볶음밥', 3000),

-- 3. 24시 수육국밥 (한식)
(3, '수육국밥', 9000),
(3, '모듬수육', 18000),
(3, '콩나물국밥', 8000),

-- 4. 고향 칼국수 (한식)
(4, '바지락칼국수', 9000),
(4, '들깨칼국수', 9500),
(4, '파전', 12000),

-- 5. 국민 낙곱새 (한식)
(5, '낙곱새', 12000),
(5, '곱창전골', 13000),
(5, '볶음밥', 3000),

-- 6. 더베이징 (중식)
(6, '짜장면', 7000),
(6, '짬뽕', 8000),
(6, '탕수육', 16000),

-- 7. 라홍방 마라탕 (중식)
(7, '마라탕', 12000),
(7, '마라샹궈', 16000),
(7, '꿔바로우', 15000),

-- 8. 회전훠궈핫 (중식)
(8, '훠궈 1인세트', 17000),
(8, '마라훠궈', 18000),
(8, '양꼬치', 13000),

-- 9. 짬뽕관 (중식)
(9, '불짬뽕', 9000),
(9, '차돌짬뽕', 10000),
(9, '군만두', 5000),

-- 10. 니뽕내뽕 (중식 퓨전)
(10, '니뽕짬뽕', 9800),
(10, '크림뽕', 10500),
(10, '로제뽕', 10800);

-- =========================================================
-- 핵심 3) review
-- =========================================================
DROP TABLE IF EXISTS `review`;
CREATE TABLE `review` (
  `review_id`    INT NOT NULL AUTO_INCREMENT,
  `user_id`      INT NOT NULL COMMENT '사용자의 id',
  `store_id`     INT NOT NULL COMMENT '매장의 id',
  `content`      TEXT,
  `rating`       TINYINT,                     -- 1~5 권장
  `helpful_cnt`  INT NOT NULL DEFAULT 0,
  `created_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  KEY `idx_review_user` (`user_id`),
  KEY `idx_review_store_created` (`store_id`, `created_at`),
  CONSTRAINT `fk_review_user`
    FOREIGN KEY (`user_id`) REFERENCES `app_user`(`user_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE,
  CONSTRAINT `fk_review_store`
    FOREIGN KEY (`store_id`) REFERENCES `store`(`store_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 샘플 리뷰(선택)
INSERT INTO `review` (user_id, store_id, content, rating, helpful_cnt)
VALUES
(1, 1, '국물 진하고 밥이랑 잘 맞음', 5, 2),
(2, 1, '양 푸짐함', 4, 1),
(3, 2, '짜장 달달함', 4, 0),
(1, 2, '짬뽕 국물이 시원', 5, 3),
(2, 3, '면 삶기 좋음', 4, 0);

-- =========================================================
-- 랭킹용 뷰(간단 평균 + 리뷰수 가중 정렬) & 고급(베이지안) 점수
-- =========================================================
-- 1) 단순 평균/리뷰수 집계 뷰
DROP VIEW IF EXISTS v_store_scores_simple;
CREATE VIEW v_store_scores_simple AS
SELECT
  s.store_id,
  s.name,
  s.address,
  s.distance_km,
  COALESCE(AVG(r.rating), 0)          AS avg_rating,
  COUNT(r.review_id)                   AS review_cnt
FROM store s
LEFT JOIN review r ON r.store_id = s.store_id
GROUP BY s.store_id, s.name, s.address, s.distance_km;


-- 2) 베이지안 평균(전체 평균으로 스무딩: m=리뷰수 임계값) 계산용 뷰
--   score = (v/(v+m))*R + (m/(v+m))*C
--   v=store 리뷰수, R=store 평균, C=전체 평균, m=임계 리뷰수(예: 5)
DROP VIEW IF EXISTS v_store_scores_bayesian;
CREATE VIEW v_store_scores_bayesian AS
WITH global_stats AS (
  SELECT
    COALESCE(AVG(rating), 0) AS C
  FROM review
),
store_stats AS (
  SELECT
    s.store_id,
    s.name,
    s.address,
    s.distance_km,
    COALESCE(AVG(r.rating), 0) AS R,
    COUNT(r.review_id)         AS v
  FROM store s
  LEFT JOIN review r ON r.store_id = s.store_id
  GROUP BY s.store_id, s.name, s.address, s.distance_km;

)
SELECT
  st.store_id,
  st.name,
  st.address,
  st.distance_km,
  st.R         AS avg_rating,
  st.v         AS review_cnt,
  -- m: 임계 리뷰수(튜닝 지점). 데이터가 적으면 3~10 사이 추천
  CAST(5 AS DECIMAL(10,2))    AS m,
  gs.C,
  ((st.v/(st.v + 5.0))*st.R + (5.0/(st.v + 5.0))*gs.C) AS bayes_score
FROM store_stats st
CROSS JOIN global_stats gs;

-- 3) 최종 랭킹(베이지안 점수 우선 → 리뷰수/평균 보조 정렬)
DROP VIEW IF EXISTS v_store_ranking;
CREATE VIEW v_store_ranking AS
SELECT
  b.store_id,
  b.name,
  b.address,
  b.distance_km,
  b.avg_rating,
  b.review_cnt,
  b.bayes_score
FROM v_store_scores_bayesian b;
-- ORDER BY b.bayes_score DESC, b.review_cnt DESC, b.avg_rating DESC, b.store_id ASC;



SELECT * FROM v_store_ranking
ORDER BY bayes_score DESC
LIMIT 5;

