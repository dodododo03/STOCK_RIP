from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Funeral(Base):
    __tablename__ = "funerals"

    id            = Column(Integer,     primary_key=True, index=True)
    ticker        = Column(String(20),  nullable=False)          # 신규: 종목 코드 (PLTR, 005930)
    title         = Column(String(100), nullable=False)          # 신규: 게시글 제목
    stock_name    = Column(String(50),  nullable=False)          # 기존 유지
    profit_rate   = Column(Float,       nullable=False)
    last_words    = Column(String(200), nullable=True)
    mourner_count = Column(Integer,     default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    comments = relationship(
        "Comment",
        back_populates="funeral",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.desc()",
    )


class Comment(Base):
    __tablename__ = "comments"

    id         = Column(Integer,     primary_key=True, index=True)
    funeral_id = Column(Integer,     ForeignKey("funerals.id"), nullable=False)
    author     = Column(String(30),  nullable=False, default="익명의 조문객")
    content    = Column(Text,        nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    funeral = relationship("Funeral", back_populates="comments")