from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from collections import Counter
import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="STOCK_RIP 주식 장례식장")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── 헬퍼 ──────────────────────────────────────────────────────────
def get_scream_level(avg_rate: float) -> str:
    if avg_rate <= -50: return "🔴 지옥문 개방"
    if avg_rate <= -30: return "🟠 절규 경보"
    if avg_rate <= -10: return "🟡 흐느낌 주의"
    return "🟢 평온 (아직은)"

def get_top3_stats(funerals: list) -> list:
    if not funerals:
        return []
    total = len(funerals)
    name_counts = Counter(f.stock_name for f in funerals)
    return [
        {"name": name, "count": count, "share": round(count / total * 100, 1)}
        for name, count in name_counts.most_common(3)
    ]


# ── GET / : 메인 페이지 ───────────────────────────────────────────
@app.get("/")
def main_page(request: Request, db: Session = Depends(get_db)):
    funerals = db.query(models.Funeral)\
                 .order_by(models.Funeral.created_at.desc())\
                 .all()
    avg_rate_result = db.query(func.avg(models.Funeral.profit_rate)).scalar()
    avg_rate = round(avg_rate_result, 2) if avg_rate_result is not None else 0.0
    return templates.TemplateResponse("index.html", {
        "request":      request,
        "funerals":     funerals,
        "avg_rate":     avg_rate,
        "scream_level": get_scream_level(avg_rate),
        "total_count":  len(funerals),
        "top3":         get_top3_stats(funerals),
    })


# ── POST /report : 사망 신고 ──────────────────────────────────────
@app.post("/report")
def report_funeral(
    request:       Request,
    stock_name:    str           = Form(...),
    avg_price:     float         = Form(...),
    current_price: float         = Form(...),
    last_words:    Optional[str] = Form(None),
    db:            Session       = Depends(get_db),
):
    profit_rate = round((current_price - avg_price) / avg_price * 100, 2)
    if profit_rate >= 0:
        funerals = db.query(models.Funeral).all()
        avg_r    = db.query(func.avg(models.Funeral.profit_rate)).scalar() or 0.0
        return templates.TemplateResponse("index.html", {
            "request":      request,
            "error":        f"수익률 {profit_rate}%는 장례식장 입장 불가입니다. 🚪",
            "funerals":     funerals,
            "avg_rate":     round(avg_r, 2),
            "scream_level": get_scream_level(avg_r),
            "total_count":  len(funerals),
            "top3":         get_top3_stats(funerals),
        })
    db.add(models.Funeral(
        stock_name=stock_name, profit_rate=profit_rate,
        last_words=last_words, mourner_count=0,
    ))
    db.commit()
    return RedirectResponse(url="/", status_code=303)


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


# ── POST /delete/{id} : 안치실 퇴실 ─────────────────────────────
@app.post("/delete/{funeral_id}")
def delete_funeral(funeral_id: int, db: Session = Depends(get_db)):
    funeral = db.get(models.Funeral, funeral_id)
    if not funeral:
        raise HTTPException(status_code=404, detail="이미 퇴실한 고인입니다.")
    db.delete(funeral)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# ── GET /room/{id} : 개별 분향소 ─────────────────────────────────
@app.get("/room/{funeral_id}")
def room_page(funeral_id: int, request: Request, db: Session = Depends(get_db)):
    """
    joinedload: Funeral을 조회할 때 Comment를 JOIN으로 한 번에 가져옴.
    lazy loading(기본값)은 comments 접근 시 SQL이 추가로 나가서 N+1 문제 발생.
    명시적으로 eager loading을 걸어주는 게 맞아.
    """
    funeral = (
        db.query(models.Funeral)
        .options(joinedload(models.Funeral.comments))
        .filter(models.Funeral.id == funeral_id)
        .first()
    )
    if not funeral:
        raise HTTPException(status_code=404, detail="존재하지 않는 분향소입니다.")

    return templates.TemplateResponse("room.html", {
        "request": request,
        "funeral": funeral,
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
    funeral = db.get(models.Funeral, funeral_id)
    if not funeral:
        raise HTTPException(status_code=404, detail="존재하지 않는 분향소입니다.")

    # 빈 content 방어
    if not content.strip():
        return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)

    db.add(models.Comment(
        funeral_id=funeral_id,
        author=author.strip() or "익명의 조문객",
        content=content.strip(),
    ))
    db.commit()
    return RedirectResponse(url=f"/room/{funeral_id}", status_code=303)