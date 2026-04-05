from pydantic import BaseModel, Field, field_validator  # 1. validator 삭제됨
from datetime import datetime
from typing import Optional

# 장례식 등록 요청용 (사망 신고)
class FuneralCreate(BaseModel):
    stock_name: str = Field(..., min_length=1, max_length=50, example="카카오")
    profit_rate: float = Field(..., example=-47.3, description="수익률 (보통 음수)")
    last_words: Optional[str] = Field(None, max_length=200, example="널 믿었건만...")

    @field_validator("profit_rate")  # 2. @validator -> @field_validator로 수정
    @classmethod                    # v2에서는 classmethod를 붙여주는 게 정석입니다!
    def rate_should_be_negative(cls, v):
        if v >= 0:
            raise ValueError("수익률이 양수면 장례식장에 올 자격이 없습니다 😤")
        return v

# 응답용 (DB 조회 결과 직렬화)
class FuneralResponse(FuneralCreate):
    id: int
    mourner_count: int
    created_at: datetime

    model_config = {"from_attributes": True}  # v2 스타일로 통일!

# ── 응답 (서버 → 클라이언트) ──────────────────────────────────────
class CommentResponse(BaseModel):
    id:         int
    nickname:   str
    content:    str
    created_at: datetime

    model_config = {"from_attributes": True}  

# ── API 공통 응답 래퍼 ────────────────────────────────────────────
class ApiResponse(BaseModel):
    success: bool
    message: str
    data:    object | None = None