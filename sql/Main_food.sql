DROP TABLE IF EXISTS category;

CREATE TABLE `category` (
  `category_id` INT NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(30) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uq_category_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기본 카테고리 데이터
INSERT INTO category (category_id, name) VALUES
(1,'한식'),
(2,'중식'),
(3,'양식'),
(4,'일식'),
(5,'분식'),
(6,'카페'),
(7,'디저트');

--------------------------------------------------
-- 2. 가게 / 메뉴 기본 테이블
--------------------------------------------------

-- 의존관계 때문에 review, menu, store 순서로 드롭
DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS menu;
DROP TABLE IF EXISTS store;

-- 가게
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

-- 메뉴
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

--------------------------------------------------
-- 3. 회원 / 관리자 관련 테이블
--------------------------------------------------

DROP TABLE IF EXISTS inquiry;
DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS provider;
DROP TABLE IF EXISTS site_admin;

-- 학생
CREATE TABLE student (
  student_id INT NOT NULL,
  major      VARCHAR(50) NOT NULL,
  PRIMARY KEY (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 매장
CREATE TABLE provider (
  pro_id          INT NOT NULL AUTO_INCREMENT,
  store_name      VARCHAR(30) NOT NULL,
  pw              VARCHAR(30) NOT NULL,
  business_number INT NOT NULL,
  status          VARCHAR(30) NOT NULL,
  login_id        VARCHAR(30) NOT NULL,
  PRIMARY KEY (pro_id),
  UNIQUE KEY uq_provider_login (login_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 사이트 관리자
CREATE TABLE site_admin (
  admin_id   INT NOT NULL AUTO_INCREMENT,
  login_id   VARCHAR(30) NOT NULL,
  pw         VARCHAR(30) NOT NULL,
  admin_name VARCHAR(30) NOT NULL,
  PRIMARY KEY (admin_id),
  UNIQUE KEY uq_site_admin_login (login_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 공통 user 테이블 (로그인용)
CREATE TABLE user (
  user_id    INT NOT NULL AUTO_INCREMENT,
  login_id   VARCHAR(30) NOT NULL UNIQUE,
  pw         VARCHAR(30) NOT NULL,
  name       VARCHAR(30) NOT NULL,
  student_id INT NULL,
  pro_id     INT NULL,
  admin_id   INT NULL,
  create_at  DATETIME DEFAULT NOW(),
  PRIMARY KEY (user_id),
  CONSTRAINT fk_user_student
    FOREIGN KEY (student_id) REFERENCES student(student_id),
  CONSTRAINT fk_user_provider
    FOREIGN KEY (pro_id) REFERENCES provider(pro_id),
  CONSTRAINT fk_user_admin
    FOREIGN KEY (admin_id) REFERENCES site_admin(admin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기본 관리자 계정 (원하면 수정해서 사용)
INSERT INTO site_admin (login_id, pw, admin_name)
VALUES ('admin01','1234','관리자1');

--------------------------------------------------
-- 4. 리뷰 / 문의 테이블 (user 참조)
--------------------------------------------------

-- 리뷰
DROP TABLE IF EXISTS review;

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
    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE,
  CONSTRAINT `fk_review_store`
    FOREIGN KEY (`store_id`) REFERENCES `store`(`store_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 문의
DROP TABLE IF EXISTS inquiry;

CREATE TABLE `inquiry` (
  `inquiry_id` INT NOT NULL AUTO_INCREMENT,
  `user_id`    INT NOT NULL COMMENT '사용자의 id',
  `title`      VARCHAR(100),
  `writer`     VARCHAR(30),
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `content`    TEXT,
  `answer`     VARCHAR(255),
  `field`      VARCHAR(255),
  PRIMARY KEY (`inquiry_id`),
  KEY `idx_inquiry_user` (`user_id`),
  CONSTRAINT `fk_inquiry_user`
    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--------------------------------------------------
-- 5. 랭킹용 뷰
--------------------------------------------------

DROP VIEW IF EXISTS v_store_ranking;
DROP VIEW IF EXISTS v_store_scores_bayesian;
DROP VIEW IF EXISTS v_store_scores_simple;

-- 단순 평균 + 리뷰수
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

-- 베이지안 점수 계산용
CREATE VIEW v_store_scores_bayesian AS
WITH global_stats AS (
  SELECT
    COALESCE(AVG(rating), 0) AS C      -- 전체 평균 평점
  FROM review
),
store_stats AS (
  SELECT
    s.store_id,
    s.name,
    s.address,
    s.distance_km,
    COALESCE(AVG(r.rating), 0) AS R,   -- 매장별 평균 평점
    COUNT(r.review_id)         AS v    -- 매장별 리뷰 수
  FROM store s
  LEFT JOIN review r ON r.store_id = s.store_id
  GROUP BY s.store_id, s.name, s.address, s.distance_km
)
SELECT
  st.store_id,
  st.name,
  st.address,
  st.distance_km,
  st.R AS avg_rating,
  st.v AS review_cnt,
  CAST(5 AS DECIMAL(10,2)) AS m,       -- 임계 리뷰 수 (튜닝 지점)
  gs.C,
  ((st.v/(st.v + 5.0))*st.R + (5.0/(st.v + 5.0))*gs.C) AS bayes_score
FROM store_stats st
CROSS JOIN global_stats gs;

-- 최종 랭킹 뷰 (백엔드에서 사용하는 뷰)
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

-- 테스트 유저 insert

INSERT INTO user (login_id, pw, name) VALUES
('user1', '1234', '테스트유저1'),
('user2', '1234', '테스트유저2'),
('user3', '1234', '테스트유저3'),
('user4', '1234', '테스트유저4'),
('user5', '1234', '테스트유저5');