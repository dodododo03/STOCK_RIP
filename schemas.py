from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class CommentCreate(BaseModel):
    author:  str = Field(default="익명의 조문객", max_length=30)
    content: str = Field(..., min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def no_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("공백만으로는 작성할 수 없습니다.")
        return v.strip()


class CommentResponse(BaseModel):
    id:         int
    author:     str
    content:    str
    created_at: datetime
    model_config = {"from_attributes": True}


class FuneralCreate(BaseModel):
    ticker:      str   = Field(..., min_length=1, max_length=20,  example="PLTR")
    title:       str   = Field(..., min_length=1, max_length=100, example="팔란티어와 함께한 1년")
    stock_name:  str   = Field(..., min_length=1, max_length=50,  example="팔란티어")
    avg_price:   float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    last_words:  Optional[str] = Field(None, max_length=200)

    @field_validator("ticker")
    @classmethod
    def upper_ticker(cls, v: str) -> str:
        return v.strip().upper()  # 종목 코드는 항상 대문자로 정규화


class FuneralResponse(BaseModel):
    id:            int
    ticker:        str
    title:         str
    stock_name:    str
    profit_rate:   float
    last_words:    Optional[str]
    mourner_count: int
    created_at:    datetime
    comments:      list[CommentResponse] = []
    model_config   = {"from_attributes": True}