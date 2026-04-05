import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 환경변수에서 DB 주소를 가져오고, 없으면 로컬용 SQLite 사용
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./stocks.db"
)

# 2. SQLite일 때만 필요한 설정 추가
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 3. 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

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