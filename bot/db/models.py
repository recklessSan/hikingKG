from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CardBatch(Base):
    __tablename__ = "card_batches"
    __table_args__ = (
        UniqueConstraint(
            "telegram_chat_id",
            "telegram_message_id",
            "bank_slug",
            "event_type",
            name="uq_batch_message_bank_event",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    event_type: Mapped[str] = mapped_column(String(16), index=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    author_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    bank: Mapped[str] = mapped_column(String(64), index=True)
    bank_slug: Mapped[str] = mapped_column(String(32), index=True)
    card_count: Mapped[int] = mapped_column(Integer)
    is_cash: Mapped[bool] = mapped_column(Boolean, default=False)
    without_lk: Mapped[bool] = mapped_column(Boolean, default=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lk_access_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    work_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    has_deposit: Mapped[bool] = mapped_column(Boolean, default=False)
    excerpt: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
