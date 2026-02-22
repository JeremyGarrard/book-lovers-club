from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events_created: Mapped[list["Event"]] = relationship("Event", back_populates="creator", cascade="all, delete-orphan")
    rsvps: Mapped[list["RSVP"]] = relationship("RSVP", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    books: Mapped[list["MemberBook"]] = relationship("MemberBook", back_populates="user", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    date: Mapped[str] = mapped_column(String(20), nullable=False)   # YYYY-MM-DD
    time: Mapped[str] = mapped_column(String(10), default="")       # HH:MM
    location: Mapped[str] = mapped_column(String(300), default="")
    book_theme: Mapped[str] = mapped_column(String(300), default="")
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    creator: Mapped["User"] = relationship("User", back_populates="events_created")
    rsvps: Mapped[list["RSVP"]] = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="event", cascade="all, delete-orphan")


class RSVP(Base):
    __tablename__ = "rsvps"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_rsvp_user_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="rsvps")
    event: Mapped["Event"] = relationship("Event", back_populates="rsvps")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="comments")
    event: Mapped["Event"] = relationship("Event", back_populates="comments")


class MemberBook(Base):
    __tablename__ = "member_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    ol_key: Mapped[str] = mapped_column(String(50), default="")      # Open Library /works/OL... key
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(300), default="")
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="books")
