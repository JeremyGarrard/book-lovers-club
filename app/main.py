import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from app.database import Base, engine
from app.models import User, Event, RSVP, Comment, MemberBook  # noqa: F401
from app.routes import auth as auth_router
from app.routes import events as events_router
from app.routes import books as books_router
from app.routes import admin as admin_router
from app.routes import mail as mail_router

from app.auth import hash_password
from app.database import SessionLocal

Base.metadata.create_all(bind=engine)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

if ADMIN_USERNAME and ADMIN_PASSWORD:
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == ADMIN_USERNAME).first():
            admin = User(
                username=ADMIN_USERNAME,
                email=f"{ADMIN_USERNAME}@admin.local",
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

app = FastAPI(title="Pittsburgh Book Lovers Club")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router.router)
app.include_router(events_router.router)
app.include_router(books_router.router)
app.include_router(admin_router.router)
app.include_router(mail_router.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from app.database import SessionLocal
    from app.models import Event
    db = SessionLocal()
    try:
        from datetime import date
        today = date.today().isoformat()
        upcoming = (
            db.query(Event)
            .filter(Event.date >= today)
            .order_by(Event.date)
            .limit(3)
            .all()
        )
    finally:
        db.close()

    # Get current user if logged in
    from app.auth import decode_token
    token = request.cookies.get("access_token")
    current_user = None
    if token:
        payload = decode_token(token)
        if payload:
            db2 = SessionLocal()
            try:
                current_user = db2.query(User).filter(User.id == int(payload["sub"])).first()
            finally:
                db2.close()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "upcoming_events": upcoming, "user": current_user},
    )


@app.get("/shop", response_class=HTMLResponse)
async def shop(request: Request):
    import os
    custom_ink_url = os.getenv("CUSTOM_INK_URL", "")

    token = request.cookies.get("access_token")
    current_user = None
    if token:
        from app.auth import decode_token
        payload = decode_token(token)
        if payload:
            db = SessionLocal()
            try:
                current_user = db.query(User).filter(User.id == int(payload["sub"])).first()
            finally:
                db.close()

    return templates.TemplateResponse(
        "shop.html",
        {"request": request, "user": current_user, "custom_ink_url": custom_ink_url},
    )
