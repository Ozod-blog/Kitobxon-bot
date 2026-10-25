from datetime import datetime, timezone
from sqlalchemy import (String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Text,
                        UniqueConstraint, Index, CheckConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(32), unique=True)
    region: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    coins: Mapped[int] = mapped_column(Integer, default=0)
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    referred_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    referrals = relationship("Referral", foreign_keys="Referral.inviter_id", back_populates="inviter")

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), index=True)
    author: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    total_pages: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class BookPage(Base):
    __tablename__ = "book_pages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("book_id", "page_number"),)

class ReadingSession(Base):
    __tablename__ = "reading_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    start_page: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    minimum_seconds: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reading_session_id: Mapped[int] = mapped_column(ForeignKey("reading_sessions.id"), unique=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text)
    correct_index: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("quiz_id", "position"),)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    correct_count: Mapped[int] = mapped_column(Integer)
    passed: Mapped[bool] = mapped_column(Boolean)
    coins_awarded: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id"))
    selected_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)

class CoinTransaction(Base):
    __tablename__ = "coin_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    operation_type: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(String(250))
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    registration_rewarded: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_rewarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="referrals")

class Gift(Base):
    __tablename__ = "gifts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    image_file_id: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class GiftOrder(Base):
    __tablename__ = "gift_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gifts.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_each: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(100))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

Index("ix_reading_user_status", ReadingSession.user_id, ReadingSession.status)
Index("ix_leaderboard", User.coins.desc(), User.total_pages.desc())
