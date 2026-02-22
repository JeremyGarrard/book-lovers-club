import httpx
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import MemberBook, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"


def _get_current_user_optional(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    from app.auth import decode_token
    payload = decode_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == int(payload["sub"])).first()


@router.get("/bookshelf", response_class=HTMLResponse)
async def bookshelf(request: Request, db: Session = Depends(get_db)):
    books = db.query(MemberBook).order_by(MemberBook.created_at.desc()).all()
    user = _get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "bookshelf.html",
        {"request": request, "books": books, "user": user},
    )


@router.get("/bookshelf/search")
async def search_books(q: str = "", request: Request = None):
    if not q.strip():
        return JSONResponse({"results": []})
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            OPEN_LIBRARY_SEARCH,
            params={"q": q, "fields": "key,title,author_name,cover_i", "limit": 10},
            timeout=10.0,
        )
    data = resp.json()
    results = []
    for doc in data.get("docs", []):
        cover_id = doc.get("cover_i")
        results.append({
            "key": doc.get("key", ""),
            "title": doc.get("title", ""),
            "author": ", ".join(doc.get("author_name", [])) or "Unknown",
            "cover_url": OPEN_LIBRARY_COVER.format(cover_id=cover_id) if cover_id else "",
        })
    return JSONResponse({"results": results})


@router.post("/bookshelf/add")
async def add_book(
    ol_key: str = Form(default=""),
    title: str = Form(...),
    author: str = Form(default=""),
    cover_url: str = Form(default=""),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = MemberBook(
        user_id=current_user.id,
        ol_key=ol_key,
        title=title,
        author=author,
        cover_url=cover_url,
        notes=notes,
    )
    db.add(book)
    db.commit()
    return RedirectResponse(url="/bookshelf", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/bookshelf/{book_id}/delete")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(MemberBook).filter(MemberBook.id == book_id).first()
    if book and (book.user_id == current_user.id or current_user.is_admin):
        db.delete(book)
        db.commit()
    return RedirectResponse(url="/bookshelf", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import RSVP, Event
    rsvps = (
        db.query(RSVP)
        .filter(RSVP.user_id == current_user.id)
        .order_by(RSVP.created_at.desc())
        .all()
    )
    books = (
        db.query(MemberBook)
        .filter(MemberBook.user_id == current_user.id)
        .order_by(MemberBook.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "rsvps": rsvps,
            "books": books,
        },
    )
