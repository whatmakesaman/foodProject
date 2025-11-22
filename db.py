import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='fooddb',   
        db='fooddb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
