from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Funeral(Base):
    __tablename__ = "funerals"

    id            = Column(Integer, primary_key=True, index=True)
    stock_name    = Column(String(50),  nullable=False)
    profit_rate   = Column(Float,       nullable=False)
    last_words    = Column(String(200), nullable=True)
    mourner_count = Column(Integer,     default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # Funeral 1 : Comment N 관계 정의
    # cascade="all, delete-orphan" → 부모(Funeral) 삭제 시 댓글도 자동 삭제
    comments = relationship(
        "Comment",
        back_populates="funeral",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.desc()"
    )


class Comment(Base):
    __tablename__ = "comments"

    id         = Column(Integer, primary_key=True, index=True)
    funeral_id = Column(Integer, ForeignKey("funerals.id"), nullable=False)
    author     = Column(String(30),  nullable=False, default="익명의 조문객")
    content    = Column(Text,        nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    funeral = relationship("Funeral", back_populates="comments")

