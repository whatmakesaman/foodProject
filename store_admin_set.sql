use fooddb;

INSERT INTO store (store_id, name, address, open, close, phone, distance)
VALUES (1, '맛있는분식', '경기도 시흥시 정왕동', '09:00', '21:00', '010-1234-5678', 1);
/*store_admin.py 테스트 진행시 sql에 입력하는 더미 데이터*/

SELECT * FROM store; /*데이터 조회용 코드*/