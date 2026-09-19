from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class College(Base):
    __tablename__ = "colleges"

    institute_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    home_university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    official_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branches: Mapped[list["Branch"]] = relationship(back_populates="college")


class Branch(Base):
    __tablename__ = "branches"

    institute_code: Mapped[str] = mapped_column(ForeignKey("colleges.institute_code"), primary_key=True)
    choice_code: Mapped[str] = mapped_column(String(12), primary_key=True)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)

    college: Mapped[College] = relationship(back_populates="branches")
    cutoff_records: Mapped[list["CutoffHistory"]] = relationship(back_populates="branch")
    seat_records: Mapped[list["SeatMatrix"]] = relationship(back_populates="branch")


class CutoffHistory(Base):
    __tablename__ = "cutoff_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institute_code: Mapped[str] = mapped_column(String(10), nullable=False)
    choice_code: Mapped[str] = mapped_column(String(12), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[str] = mapped_column(String(20), nullable=False)  # CAP1 / CAP2 / CAP3 / CAP4
    quota: Mapped[str] = mapped_column(String(20), nullable=False)  # MH / AI / DIPLOMA
    level: Mapped[str] = mapped_column(String(120), nullable=False)  # e.g. "State Level", "All India"
    stage: Mapped[str] = mapped_column(String(30), nullable=False)  # I / II / "I-Non Defence" / ...
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. GOPENS, LOBCH, EWS, TFWS, AI
    merit_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    percentile: Mapped[float] = mapped_column(Float, nullable=False)
    source_pdf: Mapped[str | None] = mapped_column(String(120), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(["institute_code", "choice_code"], ["branches.institute_code", "branches.choice_code"]),
    )

    branch: Mapped[Branch] = relationship(back_populates="cutoff_records")


class SeatMatrix(Base):
    __tablename__ = "seat_matrix"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institute_code: Mapped[str] = mapped_column(String(10), nullable=False)
    choice_code: Mapped[str] = mapped_column(String(12), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(30), nullable=False)  # State Level / PWD / DEF / Reservation
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # OPEN / SC / ST / ... / EWS / TFWS
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # G / L / TOTAL / "G + L"
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    source_pdf: Mapped[str | None] = mapped_column(String(120), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(["institute_code", "choice_code"], ["branches.institute_code", "branches.choice_code"]),
    )

    branch: Mapped[Branch] = relationship(back_populates="seat_records")


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
