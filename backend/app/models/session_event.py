import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SessionEvent(Base):
    __tablename__ = 'session_events'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text('gen_random_uuid()'))
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('play_sessions.id'), nullable=False)
    node_key: Mapped[str] = mapped_column(String(50), nullable=False)
    choice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('choices.id'), nullable=True)
    choice_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    effects: Mapped[JSONB] = mapped_column(nullable=False, server_default=text("'{}'::jsonb"))
    competency_effects: Mapped[JSONB] = mapped_column(nullable=False, server_default=text("'[]'::jsonb"))
    loyalty_after: Mapped[int] = mapped_column(nullable=False)
    safety_after: Mapped[int] = mapped_column(nullable=False)
    score_delta: Mapped[int] = mapped_column(nullable=False)
    timer_sec: Mapped[int | None] = mapped_column(nullable=True)
    timer_left_sec: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index(
            'ix_sessinon_events_session_id_created_at',
            'session_id',
            'created_at',
        ),
        Index('ix_session_events_session_id', 'session_id')
    )
