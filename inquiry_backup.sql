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
    FOREIGN KEY (`user_id`) REFERENCES `app_user`(`user_id`)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
