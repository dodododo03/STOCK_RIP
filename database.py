import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 환경변수에서 DB 주소를 가져오고, 없으면 로컬용 SQLite 사용
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./stocks.db"
)

# 2. DB 종류에 따라 연결 옵션 설정
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite용 설정
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL(Render)용 설정
    connect_args = {"sslmode": "require"}

# 3. 엔진 생성 (수정된 connect_args 사용)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args  # 골라 쓰게 합니다!
)
# 4. 세션 및 베이스 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 5. DB 세션 획득용 헬퍼 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()