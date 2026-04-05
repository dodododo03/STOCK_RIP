import os
from collections import Counter
from typing import Optional

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

import models, schemas
from database import engine, get_db

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="STOCK_RIP 주식 장례식장")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── 헬퍼 함수 ──────────────────────────────────────────────────
def get_scream_level(avg: float) -> str:
    if avg <= -50: return "🔴 지옥문 개방"
    if avg <= -30: return "🟠 절규 경보"
    if avg <= -10: return "🟡 흐느낌 주의"
    return "🟢 평온 (아직은)"

def get_top3(funerals: list) -> list:
    if not funerals: return []
    total = len(funerals)
    counts = Counter(f.stock_name for f in funerals)
    return [
        {"name": n, "count": c, "share": round(c / total * 100, 1)}
        for n, c in counts.most_common(3)
    ]

def calc_profit(avg_price: float, current_price: float) -> float:
    return round((current_price - avg_price) / avg_price * 100, 2)

# ── 라우터 ──────────────────────────────────────────────────
@app.get("/")
def main_page(request: Request, db: Session = Depends(get_db)):
    funerals = db.query(models.Funeral).order_by(models.Funeral.created_at.desc()).all()
    avg_r = db.query(func.avg(models.Funeral.profit_rate)).scalar() or 0.0
    return templates.TemplateResponse("index.html", {
        "request": request,
        "funerals": funerals,
        "avg_rate": round(avg_r, 2),
        "scream_level": get_scream_level(avg_r),
        "total_count": len(funerals),
        "top3": get_top3(funerals),
    })

@app.post("/report")
def report_funeral(
    request: Request,
    ticker: str = Form(...),
    title: str = Form(...),
    stock_name: str = Form(...),
    avg_price: float = Form(...),
    current_price: float = Form(...),
    last_words: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    profit_rate = calc_profit(avg_price, current_price)
    if profit_rate >= 0:
        return RedirectResponse(url="/?error=true", status_code=303)
    
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

@app.get("/room/{funeral_id}")
def room_page(funeral_id: int, request: Request, db: Session = Depends(get_db)):
    funeral = db.query(models.Funeral).options(joinedload(models.Funeral.comments)).filter(models.Funeral.id == funeral_id).first()
    if not funeral: raise HTTPException(status_code=404)
    return templates.TemplateResponse("room.html", {"request": request, "funeral": funeral, "comments": funeral.comments})

@app.post("/comment/{funeral_id}")
def post_comment(funeral_id: int, author: str = Form(default="익명의 조문객"), content: str = Form(...), db: Session = Depends(get_db)):
    if not content.strip(): return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)
    db.add(models.Comment(funeral_id=funeral_id, author=author.strip() or "익명의 조문객", content=content.strip()))
    db.commit()
    return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)

@app.patch("/mourn/{funeral_id}")
def mourn(funeral_id: int, db: Session = Depends(get_db)):
    funeral = db.get(models.Funeral, funeral_id)
    if not funeral: raise HTTPException(status_code=404)
    funeral.mourner_count += 1
    db.commit()
    return JSONResponse({"mourner_count": funeral.mourner_count})

@app.post("/delete/{funeral_id}")
def delete_funeral(funeral_id: int, db: Session = Depends(get_db)):
    funeral = db.get(models.Funeral, funeral_id)
    if funeral:
        db.delete(funeral)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

# ── 진입점 ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)