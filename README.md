# Backend

백앤드

# 📌 1. 실행 환경 준비

1. Python 가상환경 생성 (venv)
   > > 가상환경 설치
   ```bash
   python -m venv venv_win
   ```
2. 가상환경 실행
   ```cmd
   venv_win\Scripts\activate.bat
   ```
3. 필요한 패키지 설치
   > > 플라스크 설치
   ```bash
   pip install flask
   ```
   > > 플라스크 코어 설치
   ```bash
   pip install flask-cors
   ```
   > > pymysql 설치
   ```bash
   pip install pymysql
   ```

# 📌 2. 실행 하기

1. 자신의 실행 환경에 맞는 DB정보로 변경

2. 가상환경을 실행한 상태에서
   ```cmd
   python (실행하고자 하는 파일).py
   ```

# 📌 3. api테스트 방법

    pi_test.http에 적혀있음

# 📌 4. 폴더구조

```bash
Backend/
 ├── .vscode/
 ├── sql/
 ├── templates/
 └── README.md
```
