USE fooddb;

DROP TABLE IF EXISTS user;
CREATE TABLE user (
    user_id     INT NOT NULL AUTO_INCREMENT,
    login_id    VARCHAR(30) NOT NULL UNIQUE,
    pw          VARCHAR(30) NOT NULL,
    name        VARCHAR(30) NOT NULL,
    student_id  INT NULL,
    pro_id      INT NULL,
    admin_id    INT NULL,
    create_at   DATETIME,
    PRIMARY KEY (user_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (pro_id) REFERENCES provider(pro_id),
    FOREIGN KEY (admin_id) REFERENCES site_admin(admin_id)
);

ALTER TABLE provider 
MODIFY pro_id INT NOT NULL AUTO_INCREMENT,
ADD login_id VARCHAR(30) NOT NULL,
ADD UNIQUE (login_id);

 -- 자동으로 회원가입 날자 기입 --
ALTER TABLE user 
MODIFY create_at DATETIME DEFAULT NOW();

-- 회원가입시 마다 id 가 1 씩 자동으로 올라감 --
ALTER TABLE user 
MODIFY user_id INT NOT NULL AUTO_INCREMENT;

ALTER TABLE provider
MODIFY pro_id INT NOT NULL AUTO_INCREMENT;
select* from user;
