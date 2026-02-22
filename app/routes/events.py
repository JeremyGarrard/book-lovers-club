from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Comment, Event, RSVP, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_current_user_optional(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    from app.auth import decode_token
    payload = decode_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == int(payload["sub"])).first()


@router.get("/events", response_class=HTMLResponse)
async def events_list(request: Request, db: Session = Depends(get_db)):
    from datetime import date
    today = date.today().isoformat()
    upcoming = db.query(Event).filter(Event.date >= today).order_by(Event.date).all()
    past = db.query(Event).filter(Event.date < today).order_by(Event.date.desc()).limit(10).all()
    user = _get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "events.html",
        {"request": request, "upcoming": upcoming, "past": past, "user": user},
    )


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(event_id: int, request: Request, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return RedirectResponse(url="/events", status_code=status.HTTP_303_SEE_OTHER)

    user = _get_current_user_optional(request, db)
    rsvp_count = db.query(RSVP).filter(RSVP.event_id == event_id).count()
    user_rsvped = False
    if user:
        user_rsvped = db.query(RSVP).filter(
            RSVP.event_id == event_id, RSVP.user_id == user.id
        ).first() is not None

    comments = (
        db.query(Comment)
        .filter(Comment.event_id == event_id)
        .order_by(Comment.created_at)
        .all()
    )

    return templates.TemplateResponse(
        "event_detail.html",
        {
            "request": request,
            "event": event,
            "user": user,
            "rsvp_count": rsvp_count,
            "user_rsvped": user_rsvped,
            "comments": comments,
        },
    )


@router.post("/events/{event_id}/rsvp")
async def toggle_rsvp(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(RSVP).filter(
        RSVP.event_id == event_id, RSVP.user_id == current_user.id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    else:
        rsvp = RSVP(user_id=current_user.id, event_id=event_id)
        db.add(rsvp)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return RedirectResponse(url=f"/events/{event_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/events/{event_id}/comment")
async def post_comment(
    event_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if content.strip():
        comment = Comment(
            user_id=current_user.id,
            event_id=event_id,
            content=content.strip(),
        )
        db.add(comment)
        db.commit()
    return RedirectResponse(url=f"/events/{event_id}", status_code=status.HTTP_303_SEE_OTHER)
