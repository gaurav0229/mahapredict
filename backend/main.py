from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.orm import Session

from database import get_db
from models import Branch, College, CutoffHistory, SeatMatrix

app = FastAPI(
    title="Maharashtra Engineering Admission Predictor API",
    version="2.0.0",
    description="Admissions and cutoff prediction API backed by real MHT-CET CAP cutoff and seat-matrix data (2023-2026).",
)

allowed_origins = (
    os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://mahapredict.vercel.app").split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORY_OPTIONS = [
    "GOPEN",
    "GOBSC",
    "GOSC",
    "GOST",
    "LOPEN",
    "LOBSC",
    "LOSC",
    "LOST",
    "EWS",
    "TFWS",
]

# The frontend's simplified category list maps to the real MHT-CET CAP category
# codes used in cutoff_history (State Level, MH quota). The real data also has
# VJ/NT1/NT2/NT3/SEBC/PWD/DEF variants and Home-University-specific levels that
# aren't exposed as options yet - extending CATEGORY_OPTIONS/CATEGORY_MAP together
# is how to add them later.
CATEGORY_MAP: dict[str, str] = {
    "GOPEN": "GOPENS",
    "GOBSC": "GOBCS",
    "GOSC": "GSCS",
    "GOST": "GSTS",
    "LOPEN": "LOPENS",
    "LOBSC": "LOBCS",
    "LOSC": "LSCS",
    "LOST": "LSTS",
    "EWS": "EWS",
    "TFWS": "TFWS",
}

# Same mapping but into seat_matrix's (category, gender, level) shape, which uses
# a different, coarser vocabulary (OPEN/OBC/SC/ST + G/L) than cutoff_history's
# combined codes (GOPENS/LOBCS/...). EWS and TFWS are recorded as single "Reservation"
# totals rather than split by gender.
SEAT_CATEGORY_MAP: dict[str, tuple[str, str, str]] = {
    "GOPEN": ("OPEN", "G", "State Level"),
    "LOPEN": ("OPEN", "L", "State Level"),
    "GOBSC": ("OBC", "G", "State Level"),
    "LOBSC": ("OBC", "L", "State Level"),
    "GOSC": ("SC", "G", "State Level"),
    "LOSC": ("SC", "L", "State Level"),
    "GOST": ("ST", "G", "State Level"),
    "LOST": ("ST", "L", "State Level"),
    "EWS": ("EWS", "TOTAL", "Reservation"),
    "TFWS": ("TFWS", "TOTAL", "Reservation"),
}

CHANCE_RANK = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "NOT_ELIGIBLE": 3}

request_log: dict[str, list[float]] = defaultdict(list)


def _latest_data_year(db: Session) -> int:
    year = db.execute(select(func.max(CutoffHistory.year))).scalar()
    return year or 2026


class StudentProfile(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=255)
    student_type: Literal["12th", "diploma"] = "12th"
    city: str = Field(default="Pune", max_length=80)
    domicile: Literal["Maharashtra", "Non-Maharashtra"] = "Maharashtra"
    hsc_percentage: float | None = Field(default=None, ge=40, le=100)
    # MHT-CET *percentile* (0-100), not the raw 200-mark score - cutoff_history stores
    # percentiles, so that's what a student's input needs to be comparable against.
    cet_percentile: float | None = Field(default=None, ge=0, le=100)
    jee_score: float | None = Field(default=None, ge=0, le=400)
    # Approximation: the official DIPLOMA-quota merit list is itself percentile-ranked
    # (see cutoff_history where quota='DIPLOMA'), not the same axis as a diploma
    # marksheet percentage. We don't have a marks->percentile converter for diploma
    # holders, so this value is used directly as a percentile proxy for comparison.
    diploma_percentage: float | None = Field(default=None, ge=40, le=100)
    category: str = Field(..., pattern=r"^(GOPEN|GOBSC|GOSC|GOST|LOPEN|LOBSC|LOSC|LOST|EWS|TFWS)$")
    preferred_branches: list[str] = Field(default_factory=lambda: ["Computer Science", "Information Technology", "Electronics"])
    preferred_districts: list[str] = Field(default_factory=lambda: ["Pune", "Mumbai", "Nagpur"])

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        if re.search(r"[<>;\-\-]|(script)|(<\/)|\|\|", value, re.IGNORECASE):
            raise ValueError("Invalid characters in name")
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")
        return value.strip().lower()


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    request_log[client_ip] = [t for t in request_log.get(client_ip, []) if now - t < 60]

    if len(request_log[client_ip]) >= 60:
        return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again later."})

    request_log[client_ip].append(now)

    if request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 200000:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})

    return await call_next(request)


def classify_score(score: float, cutoff: float) -> str:
    if score >= cutoff:
        return "HIGH"
    if score >= cutoff - 3:
        return "MODERATE"
    if score >= cutoff - 7:
        return "LOW"
    return "NOT_ELIGIBLE"


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "message": "Admission predictor backend is running"}


@app.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    latest_year = _latest_data_year(db)
    total_colleges = db.execute(select(func.count()).select_from(College)).scalar() or 0
    total_branches = db.execute(select(func.count()).select_from(Branch)).scalar() or 0

    top_colleges = db.execute(
        select(func.count(func.distinct(CutoffHistory.institute_code))).where(
            CutoffHistory.category == "GOPENS",
            CutoffHistory.quota == "MH",
            CutoffHistory.level == "State Level",
            CutoffHistory.year == latest_year,
            CutoffHistory.percentile >= 85,
        )
    ).scalar() or 0

    status_breakdown = db.execute(
        select(College.status, func.count()).group_by(College.status).order_by(func.count().desc())
    ).all()

    return {
        "total_colleges": total_colleges,
        "total_branches": total_branches,
        "top_colleges": top_colleges,
        "data_year": latest_year,
        "college_status_breakdown": [
            {"name": status or "Unknown", "value": count} for status, count in status_breakdown if count
        ],
    }


@app.get("/colleges")
def get_colleges(
    branch: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    base_query = select(College)
    count_query = select(func.count(func.distinct(College.institute_code)))
    if branch:
        base_query = base_query.join(Branch, Branch.institute_code == College.institute_code).where(
            Branch.course_name.ilike(f"%{branch}%")
        )
        count_query = count_query.select_from(College).join(
            Branch, Branch.institute_code == College.institute_code
        ).where(Branch.course_name.ilike(f"%{branch}%"))

    total = db.execute(count_query).scalar() or 0
    query = base_query.distinct().order_by(College.name).limit(limit).offset(offset)

    colleges = db.execute(query).scalars().unique().all()
    results = [
        {
            "id": college.institute_code,
            "name": college.name,
            "status": college.status,
            "home_university": college.home_university,
            "website": college.official_website,
            "branches": [b.course_name for b in college.branches],
        }
        for college in colleges
    ]
    return {"count": len(results), "total": total, "limit": limit, "offset": offset, "items": results}


@app.get("/colleges/{institute_code}")
def get_college(institute_code: str, db: Session = Depends(get_db)):
    college = db.get(College, institute_code)
    if college is None:
        raise HTTPException(status_code=404, detail="College not found")

    latest_year = _latest_data_year(db)
    cutoffs = db.execute(
        select(CutoffHistory)
        .where(
            CutoffHistory.institute_code == institute_code,
            CutoffHistory.quota == "MH",
            CutoffHistory.level == "State Level",
            CutoffHistory.year == latest_year,
            CutoffHistory.category == "GOPENS",
        )
    ).scalars().all()
    cutoff_by_choice = {c.choice_code: c.percentile for c in cutoffs}

    return {
        "id": college.institute_code,
        "name": college.name,
        "status": college.status,
        "home_university": college.home_university,
        "website": college.official_website,
        "branches": [
            {
                "choice_code": b.choice_code,
                "course_name": b.course_name,
                "latest_gopen_state_percentile": cutoff_by_choice.get(b.choice_code),
            }
            for b in college.branches
        ],
    }


@app.post("/predict")
def predict_colleges(payload: StudentProfile, db: Session = Depends(get_db)):
    if payload.student_type == "12th":
        score = payload.cet_percentile or payload.hsc_percentage or 0
    else:
        score = payload.diploma_percentage or 0

    if score <= 0:
        raise HTTPException(status_code=400, detail="Please provide a valid CET percentile or academic score.")

    latest_year = _latest_data_year(db)

    if payload.student_type == "diploma":
        quota = "DIPLOMA"
        category_filter = None
    else:
        quota = "MH"
        category_filter = CATEGORY_MAP.get(payload.category)
        if not category_filter:
            raise HTTPException(status_code=400, detail="Unsupported category.")

    query = (
        select(
            Branch.institute_code,
            Branch.choice_code,
            Branch.course_name,
            College.name.label("college_name"),
            College.status,
            College.home_university,
            College.official_website,
            CutoffHistory.year,
            CutoffHistory.round,
            CutoffHistory.percentile,
            CutoffHistory.merit_rank,
        )
        .join(College, College.institute_code == Branch.institute_code)
        .join(
            CutoffHistory,
            (CutoffHistory.institute_code == Branch.institute_code) & (CutoffHistory.choice_code == Branch.choice_code),
        )
        .where(CutoffHistory.quota == quota)
    )
    if quota == "MH":
        query = query.where(CutoffHistory.category == category_filter, CutoffHistory.level == "State Level")
    else:
        query = query.where(CutoffHistory.level == "Diploma")

    branch_patterns = [f"%{b.strip()}%" for b in payload.preferred_branches if b.strip()]
    if branch_patterns:
        query = query.where(or_(*[Branch.course_name.ilike(p) for p in branch_patterns]))

    query = query.order_by(Branch.institute_code, Branch.choice_code, CutoffHistory.year.desc(), CutoffHistory.round.desc())

    rows = db.execute(query).all()

    grouped: dict[tuple[str, str], list] = {}
    for row in rows:
        grouped.setdefault((row.institute_code, row.choice_code), []).append(row)

    # Batch-fetch seat counts for every matched branch in one query instead of N+1.
    seats_by_branch: dict[tuple[str, str], int] = {}
    if payload.student_type != "diploma" and payload.category in SEAT_CATEGORY_MAP and grouped:
        seat_cat, seat_gender, seat_level = SEAT_CATEGORY_MAP[payload.category]
        keys = list(grouped.keys())
        seat_rows = db.execute(
            select(SeatMatrix.institute_code, SeatMatrix.choice_code, func.sum(SeatMatrix.seats))
            .where(
                tuple_(SeatMatrix.institute_code, SeatMatrix.choice_code).in_(keys),
                SeatMatrix.category == seat_cat,
                SeatMatrix.gender == seat_gender,
                SeatMatrix.level == seat_level,
                SeatMatrix.year == latest_year,
            )
            .group_by(SeatMatrix.institute_code, SeatMatrix.choice_code)
        ).all()
        seats_by_branch = {(r[0], r[1]): r[2] for r in seat_rows}

    matches = []
    for (institute_code, choice_code), group_rows in grouped.items():
        latest = group_rows[0]  # rows are ordered year DESC, round DESC per group
        history = [{"year": r.year, "round": r.round, "percentile": round(r.percentile, 2)} for r in group_rows]

        trend = "stable"
        distinct_years = sorted({r.year for r in group_rows}, reverse=True)
        if len(distinct_years) >= 2:
            prev_row = next((r for r in group_rows if r.year == distinct_years[1]), None)
            if prev_row:
                diff = latest.percentile - prev_row.percentile
                trend = "up" if diff > 0.5 else "down" if diff < -0.5 else "stable"

        chance = classify_score(score, latest.percentile)

        matches.append(
            {
                "id": f"{institute_code}-{choice_code}",
                "college_name": latest.college_name,
                "status": latest.status,
                "home_university": latest.home_university,
                "website": latest.official_website,
                "branch": latest.course_name,
                "category": payload.category,
                "cutoff": round(latest.percentile, 2),
                "cutoff_year": latest.year,
                "cutoff_round": latest.round,
                "your_score": round(score, 2),
                "chance": chance,
                "trend": trend,
                "seats_available": seats_by_branch.get((institute_code, choice_code)),
                "cutoff_history": history,
            }
        )

    matches.sort(key=lambda item: (CHANCE_RANK[item["chance"]], -item["cutoff"]))

    summary = {
        "total_colleges": len(matches),
        "high_chance": sum(1 for item in matches if item["chance"] == "HIGH"),
        "moderate_chance": sum(1 for item in matches if item["chance"] == "MODERATE"),
        "low_chance": sum(1 for item in matches if item["chance"] == "LOW"),
        "not_eligible": sum(1 for item in matches if item["chance"] == "NOT_ELIGIBLE"),
    }

    recommended = [
        {
            "id": item["id"],
            "college_name": item["college_name"],
            "branch": item["branch"],
            "chance": item["chance"],
            "cutoff": item["cutoff"],
        }
        for item in matches[:5]
    ]

    return {
        "student_name": payload.full_name,
        "student_type": payload.student_type,
        "category": payload.category,
        "score_used": round(score, 2),
        "data_year": latest_year,
        "summary": summary,
        "colleges": matches[:10],
        "recommended": recommended,
    }
