from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

# 장례식 등록 요청용 (사망 신고)
class FuneralCreate(BaseModel):
    stock_name: str = Field(..., min_length=1, max_length=50, example="카카오")
    profit_rate: float = Field(..., example=-47.3, description="수익률 (보통 음수)")
    last_words: Optional[str] = Field(None, max_length=200, example="널 믿었건만...")

    @validator("profit_rate")
    def rate_should_be_negative(cls, v):
        if v >= 0:
            raise ValueError("수익률이 양수면 장례식장에 올 자격이 없습니다 😤")
        return v

# 응답용 (DB 조회 결과 직렬화)
class FuneralResponse(FuneralCreate):
    id: int
    mourner_count: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (구버전은 orm_mode = True)
# 공백만 입력하는 어뷰징 방어
    @field_validator("nickname", "content")
    @classmethod
    def strip_and_check_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("공백만으로는 작성할 수 없습니다.")
        return v

# ── 응답 (서버 → 클라이언트) ──────────────────────────────────────
class CommentResponse(BaseModel):
    id:         int
    nickname:   str
    content:    str
    created_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2 ORM 직렬화     


# ── API 공통 응답 래퍼 ────────────────────────────────────────────
class ApiResponse(BaseModel):
    """
    { "success": true, "message": "...", "data": {...} }
    일관된 응답 포맷은 프론트엔드가 에러 핸들링을 예측 가능하게 만들어.
    실무에서 프론트-백 협업할 때 제일 먼저 합의해야 할 부분이야.
    """
    success: bool
    message: str
    data:    object | None = None
#``

#> **`FuneralResponse`가 `FuneralCreate`를 상속받는 이유**
#> 입력 스키마와 응답 스키마를 분리하는 건 실무 기본 패턴이야. 입력에는 없는 `id`, `created_at` 같은 **서버 생성 필드**는 응답 스키마에만 존재해야 해. 나중에 `password` 같은 민감 필드를 응답에서 제외할 때도 이 구조가 유용해.

#---

## 구조 요약
#```
#FuneralCreate  →  DB 저장 (입력 검증)
#FuneralResponse →  클라이언트 반환 (ORM 객체 직렬화)
#Funeral (Model) →  실제 DB 테이블 매핑
#'''