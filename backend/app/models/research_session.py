from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user = relationship("User")
    sources = relationship(
        "Source", back_populates="session", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )
    infographic = relationship(
        "Infographic",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
