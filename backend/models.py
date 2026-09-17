from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    college_type: Mapped[str] = mapped_column(String(80), nullable=False)
    official_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_seats: Mapped[int] = mapped_column(Integer, default=0)
    average_cutoff: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch_records: Mapped[list["Branch"]] = relationship(back_populates="college")
    cutoff_records: Mapped[list["CutoffHistory"]] = relationship(back_populates="college")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    college_id: Mapped[str] = mapped_column(ForeignKey("colleges.id"), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    intake: Mapped[int | None] = mapped_column(Integer, nullable=True)
    placement_signal: Mapped[str | None] = mapped_column(String(80), nullable=True)

    college: Mapped[College] = relationship(back_populates="branch_records")


class CutoffHistory(Base):
    __tablename__ = "cutoff_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    college_id: Mapped[str] = mapped_column(ForeignKey("colleges.id"), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    cutoff_percent: Mapped[float] = mapped_column(Float, nullable=False)
    closing_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trend_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    college: Mapped[College] = relationship(back_populates="cutoff_records")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SavedPrediction(Base):
    __tablename__ = "saved_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    percentile: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    preferred_branches: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
