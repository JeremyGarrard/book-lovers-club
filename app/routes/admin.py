from datetime import date

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Comment, Event, MemberBook, RSVP, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_view(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at).all()
    events = db.query(Event).order_by(Event.date.desc()).all()
    today = date.today().isoformat()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": current_user,
            "users": users,
            "events": events,
            "today": today,
        },
    )


@router.post("/admin/events")
async def create_event(
    title: str = Form(...),
    description: str = Form(default=""),
    date: str = Form(...),
    time: str = Form(default=""),
    location: str = Form(default=""),
    book_theme: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    event = Event(
        title=title,
        description=description,
        date=date,
        time=time,
        location=location,
        book_theme=book_theme,
        created_by=current_user.id,
    )
    db.add(event)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/events/{event_id}/delete")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_admin = not user.is_admin
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
