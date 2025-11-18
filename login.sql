USE fooddb;

-- 관리자 로그인 --

ALTER TABLE site_admin
ADD COLUMN login_id VARCHAR(30),
ADD COLUMN pw VARCHAR(30),
ADD COLUMN admin_name VARCHAR(30);

-- 관리자 계정 --

ALTER TABLE site_admin
MODIFY admin_id INT NOT NULL AUTO_INCREMENT;

INSERT INTO site_admin (admin_id, login_id, pw, admin_name)
VALUES (1, 'admin01', '1234', '관리자1');