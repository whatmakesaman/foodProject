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
INSERT INTO `store` (name, address, open_time, close_time, phone, distance_km, category_id)
VALUES
('철수네 김치찌개', '경기 시흥시 정왕동 1', '10:00','22:00','010-1111-2222', 0.8, 1),
('진짜짜장',      '경기 시흥시 정왕동 2', '11:00','21:30','010-3333-4444', 1.2, 2),
('파스타비',       '경기 시흥시 정왕동 3', '11:30','22:30','010-5555-6666', 1.8, 3);

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
INSERT INTO `menu` (store_id, name, price, recommend)
VALUES
(1, '김치찌개', 9000, '보통맵기'),
(1, '제육볶음', 9500, NULL),
(2, '짜장면',   7000, '곱빼기'),
(2, '짬뽕',     8000, NULL),
(3, '봉골레',  14000, NULL),
(3, '알리오올리오', 12000, '추천');

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
GROUP BY s.store_id;

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
  GROUP BY s.store_id
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
FROM v_store_scores_bayesian b
ORDER BY b.bayes_score DESC, b.review_cnt DESC, b.avg_rating DESC, b.store_id ASC;



USE fooddb;
SHOW TABLES;
SELECT * FROM  v_store_ranking LIMIT 5;
