import os
from collections import Counter

from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="STOCK_RIP 주식 장례식장")

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 배포 후 실제 도메인으로 교체
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── 헬퍼 ──────────────────────────────────────────────────────────
def get_scream_level(avg: float) -> str:
    if avg <= -50: return "🔴 지옥문 개방"
    if avg <= -30: return "🟠 절규 경보"
    if avg <= -10: return "🟡 흐느낌 주의"
    return "🟢 평온 (아직은)"

def get_top3(funerals: list) -> list:
    if not funerals:
        return []
    total = len(funerals)
    counts = Counter(f.stock_name for f in funerals)
    return [
        {"name": n, "count": c, "share": round(c / total * 100, 1)}
        for n, c in counts.most_common(3)
    ]

def calc_profit(avg_price: float, current_price: float) -> float:
    return round((current_price - avg_price) / avg_price * 100, 2)


# ── GET / : 메인 ──────────────────────────────────────────────────
@app.get("/")
def main_page(request: Request, db: Session = Depends(get_db)):
    funerals = (
        db.query(models.Funeral)
        .order_by(models.Funeral.created_at.desc())
        .all()
    )
    avg_r = db.query(func.avg(models.Funeral.profit_rate)).scalar() or 0.0
    avg_r = round(avg_r, 2)

    return templates.TemplateResponse("index.html", {
        "request":      request,
        "funerals":     funerals,
        "avg_rate":     avg_r,
        "scream_level": get_scream_level(avg_r),
        "total_count":  len(funerals),
        "top3":         get_top3(funerals),
    })


# ── POST /report : 사망 신고 ──────────────────────────`───────────
@app.post("/report")
def report_funeral(
    request:       Request,
    ticker:        str           = Form(...),
    title:         str           = Form(...),``
    stock_name:    str           = Form(...),
    avg_price:     float         = Form(...),
    current_price: float         = Form(...),
    last_words:    Optional[str] = Form(None),
    db:            Session       = Depends(get_db),
):
    profit_rate = calc_profit(avg_price, current_price)

    if profit_rate >= 0:
        funerals = db.query(models.Funeral).all()
        avg_r    = db.query(func.avg(models.Funeral.profit_rate)).scalar() or 0.0
        return templates.TemplateResponse("index.html", {
            "request":      request,
            "error":        f"수익률 {profit_rate}%는 입장 불가입니다. 🚪",
            "funerals":     funerals,
            "avg_rate":     round(avg_r, 2),
            "scream_level": get_scream_level(avg_r),
            "total_count":  len(funerals),
            "top3":         get_top3(funerals),
        })

    db.add(models.Funeral(
        ticker=ticker.strip().upper(),
        title=title.strip(),
        stock_name=stock_name.strip(),
        profit_rate=profit_rate,
        last_words=last_words,
        mourner_count=0,
    ))
    db.commit()
    return RedirectResponse(url="/", status_code=303)

#a
# ── GET /room/{id} : 분향소 ──────────────────────────────────────
@app.get("/room/{funeral_id}")
def room_page(funeral_id: int, request: Request, db: Session = Depends(get_db)):
    funeral = (
        db.query(models.Funeral)
        .options(joinedload(models.Funeral.comments))
        .filter(models.Funeral.id == funeral_id)
        .first()
    )
    if not funeral:
        raise HTTPException(status_code=404, detail="존재하지 않는 분향소입니다.")

    return templates.TemplateResponse("room.html", {
        "request":  request,
        "funeral":  funeral,
        "comments": funeral.comments,
    })


# ── POST /comment/{id} : 방명록 작성 ────────────────────────────
@app.post("/comment/{funeral_id}")
def post_comment(
    funeral_id: int,
    author:     str = Form(default="익명의 조문객"),
    content:    str = Form(...),
    db:         Session = Depends(get_db),
):
    if not content.strip():
        return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)

    funeral = db.get(models.Funeral, funeral_id)
    if not funeral:
        raise HTTPException(status_code=404)

    db.add(models.Comment(
        funeral_id=funeral_id,
        author=author.strip() or "익명의 조문객",
        content=content.strip(),
    ))
    db.commit()
    return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)


# ── PATCH /mourn/{id} : 헌화 ─────────────────────────────────────
@app.patch("/mourn/{funeral_id}")
def mourn(funeral_id: int, db: Session = Depends(get_db)):
    funeral = db.get(models.Funeral, funeral_id)
    if not funeral:
        raise HTTPException(status_code=404, detail="해당 종목을 찾을 수 없습니다.")
    funeral.mourner_count += 1
    db.commit()
    db.refresh(funeral)
    return JSONResponse({"mourner_count": funeral.mourner_count})


# ── POST /delete/{id} : 삭제 ─────────────────────────────────────
@app.post("/delete/{funeral_id}")
def delete_funeral(funeral_id: int, db: Session = Depends(get_db)):
    funeral = db.get(models.Funeral, funeral_id)
    if not funeral:
        raise HTTPException(status_code=404)
    db.delete(funeral)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# ── API: 게시글 목록 JSON ([ticker] title 포맷) ──────────────────
@app.get("/api/funerals", response_model=list[schemas.FuneralResponse])
def api_list(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    외부 연동이나 프론트 SPA 전환 시 사용.
    "[PLTR] 팔란티어와 함께한 1년" 포맷은 프론트에서 조합하거나
    여기서 formatted_title 필드를 추가해서 내려줄 수 있다.
    """
    return (
        db.query(models.Funeral)
        .options(joinedload(models.Funeral.comments))
        .order_by(models.Funeral.created_at.desc())
        .offset(skip).limit(limit)
        .all()
    )


# ── 진입점: 배포 환경 PORT 환경변수 대응 ─────────────────────────
if __name__ == "__main__":
    import uvicorn
    import os
    # Render는 PORT 환경변수를 주입하므로, 없으면 기본값 10000을 사용합니다.
    port = int(os.environ.get("PORT", 10000)) 
    # 배포 환경에서는 "main:app" 문자열 대신 객체 app을 직접 넘기는 게 더 안전합니다.
    uvicorn.run(app, host="0.0.0.0", port=port)