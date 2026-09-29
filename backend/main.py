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
    "GVJ",
    "GNT1",
    "GNT2",
    "GNT3",
    "GSEBC",
    "LOPEN",
    "LOBSC",
    "LOSC",
    "LOST",
    "LVJ",
    "LNT1",
    "LNT2",
    "LNT3",
    "LSEBC",
    "EWS",
    "TFWS",
]

# The frontend's category list maps to the real MHT-CET CAP category codes used in
# cutoff_history (State Level, MH quota). NT1/NT2/NT3 correspond to seat_matrix's
# NTB/NTC/NTD (confirmed by column position in the official PDFs - both list
# OPEN/SC/ST/VJ/NT-B/NT-C/NT-D/OBC/SEBC in that same order). PWD and DEF (disability/
# defence reservation) are a separate dimension layered across any of these castes
# (e.g. PWDOBCS) rather than another caste option, and aren't exposed as a selector yet.
CATEGORY_MAP: dict[str, str] = {
    "GOPEN": "GOPENS", "GOBSC": "GOBCS", "GOSC": "GSCS", "GOST": "GSTS",
    "GVJ": "GVJS", "GNT1": "GNT1S", "GNT2": "GNT2S", "GNT3": "GNT3S", "GSEBC": "GSEBCS",
    "LOPEN": "LOPENS", "LOBSC": "LOBCS", "LOSC": "LSCS", "LOST": "LSTS",
    "LVJ": "LVJS", "LNT1": "LNT1S", "LNT2": "LNT2S", "LNT3": "LNT3S", "LSEBC": "LSEBCS",
    "EWS": "EWS", "TFWS": "TFWS",
}

# Same mapping but into seat_matrix's (category, gender, level) shape, which uses
# a different, coarser vocabulary (OPEN/SC/ST/VJ/DT/NTB/NTC/NTD/OBC/SEBC + G/L) than
# cutoff_history's combined codes (GOPENS/LOBCS/...). EWS and TFWS are recorded as
# single "Reservation" totals rather than split by gender.
SEAT_CATEGORY_MAP: dict[str, tuple[str, str, str]] = {
    "GOPEN": ("OPEN", "G", "State Level"), "LOPEN": ("OPEN", "L", "State Level"),
    "GOBSC": ("OBC", "G", "State Level"), "LOBSC": ("OBC", "L", "State Level"),
    "GOSC": ("SC", "G", "State Level"), "LOSC": ("SC", "L", "State Level"),
    "GOST": ("ST", "G", "State Level"), "LOST": ("ST", "L", "State Level"),
    "GVJ": ("VJ/DT", "G", "State Level"), "LVJ": ("VJ/DT", "L", "State Level"),
    "GNT1": ("NTB", "G", "State Level"), "LNT1": ("NTB", "L", "State Level"),
    "GNT2": ("NTC", "G", "State Level"), "LNT2": ("NTC", "L", "State Level"),
    "GNT3": ("NTD", "G", "State Level"), "LNT3": ("NTD", "L", "State Level"),
    "GSEBC": ("SEBC", "G", "State Level"), "LSEBC": ("SEBC", "L", "State Level"),
    "EWS": ("EWS", "TOTAL", "Reservation"),
    "TFWS": ("TFWS", "TOTAL", "Reservation"),
}

# Same category, but the H/O-suffixed variants used by the four Home-University-aware
# levels below (EWS/TFWS have no H/O split in the data - State Level only).
CATEGORY_MAP_HOME: dict[str, str] = {
    "GOPEN": "GOPENH", "GOBSC": "GOBCH", "GOSC": "GSCH", "GOST": "GSTH",
    "GVJ": "GVJH", "GNT1": "GNT1H", "GNT2": "GNT2H", "GNT3": "GNT3H", "GSEBC": "GSEBCH",
    "LOPEN": "LOPENH", "LOBSC": "LOBCH", "LOSC": "LSCH", "LOST": "LSTH",
    "LVJ": "LVJH", "LNT1": "LNT1H", "LNT2": "LNT2H", "LNT3": "LNT3H", "LSEBC": "LSEBCH",
}
CATEGORY_MAP_OTHER: dict[str, str] = {
    "GOPEN": "GOPENO", "GOBSC": "GOBCO", "GOSC": "GSCO", "GOST": "GSTO",
    "GVJ": "GVJO", "GNT1": "GNT1O", "GNT2": "GNT2O", "GNT3": "GNT3O", "GSEBC": "GSEBCO",
    "LOPEN": "LOPENO", "LOBSC": "LOBCO", "LOSC": "LSCO", "LOST": "LSTO",
    "LVJ": "LVJO", "LNT1": "LNT1O", "LNT2": "LNT2O", "LNT3": "LNT3O", "LSEBC": "LSEBCO",
}

# A college's seats aren't just "State Level" - Maharashtra CAP also reserves seats by
# which university the COLLEGE belongs to ("home" seats) vs not ("other" seats), and
# separately by which university the CANDIDATE is from. That's a 2x2 matrix, and for a
# candidate whose home university matches the college's, the "home seats for home
# candidates" cutoff is usually meaningfully easier than State Level - a predictor that
# only ever checks State Level understates their real chances. category suffix (H/O)
# tracks which SEAT pool; the level string additionally tracks which CANDIDATE pool.
LEVEL_HOME_TO_HOME = "Home University Seats Allotted to Home University Candidates"
LEVEL_HOME_TO_OTHER = "Home University Seats Allotted to Other Than Home University Candidates"
LEVEL_OTHER_TO_HOME = "Other Than Home University Seats Allotted to Home University Candidates"
LEVEL_OTHER_TO_OTHER = "Other Than Home University Seats Allotted to Other Than Home University Candidates"
# Colleges with no real home-university affiliation (autonomous institutes, deemed
# universities) only ever publish a State Level table - the H/O split doesn't apply.
NON_AFFILIATED_HOME_UNIVERSITY_VALUES = {None, "", "Autonomous Institute", "Deemed to be University"}

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
    # JEE(Main) NTA *percentile score* (0-100), not raw marks - the AI-quota cutoff PDFs
    # report JEE-based rows on this same percentile scale (see cutoff_history.merit_exam).
    jee_percentile: float | None = Field(default=None, ge=0, le=100)
    # Approximation: the official DIPLOMA-quota merit list is itself percentile-ranked
    # (see cutoff_history where quota='DIPLOMA'), not the same axis as a diploma
    # marksheet percentage. We don't have a marks->percentile converter for diploma
    # holders, so this value is used directly as a percentile proxy for comparison.
    diploma_percentage: float | None = Field(default=None, ge=40, le=100)
    category: str = Field(
        ...,
        pattern=r"^(GOPEN|GOBSC|GOSC|GOST|GVJ|GNT1|GNT2|GNT3|GSEBC|LOPEN|LOBSC|LOSC|LOST|LVJ|LNT1|LNT2|LNT3|LSEBC|EWS|TFWS)$",
    )
    # MH: regular Maharashtra state quota (default, category-based). AI: All-India quota
    # seats, merit-based on whichever of jee_percentile/cet_percentile is provided -
    # category is not applied (AI-quota seats aren't split by caste/gender the way MH
    # quota is, beyond a small reserved-category subset not yet exposed here).
    quota: Literal["MH", "AI"] = "MH"
    # Which university the student's qualifying school/college (12th or diploma) is
    # affiliated with - determines Home-University-seat eligibility (see
    # CATEGORY_MAP_HOME / LEVEL_HOME_TO_HOME etc.). Optional - if omitted, predictions
    # fall back to State-Level-only comparison as before.
    home_university: str | None = Field(default=None, max_length=255)
    preferred_branches: list[str] = Field(default_factory=lambda: ["Computer Science", "Information Technology", "Electronics"])
    # Specific colleges (institute_code) the student wants checked, e.g. a shortlist they
    # already have in mind - when given, results are restricted to just these colleges
    # (still narrowed further by preferred_branches if that's also non-empty).
    preferred_colleges: list[str] = Field(default_factory=list)
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


@app.get("/universities")
def get_universities(db: Session = Depends(get_db)) -> dict:
    """Real Maharashtra university names, for the predictor's Home University selector -
    excludes autonomous/deemed institutes, which have no home-university seat split."""
    # SQL's NOT IN treats a NULL in the list as "unknown" for every row, matching nothing -
    # exclude None from the set explicitly rather than relying on NOT IN to do it.
    excluded = [v for v in NON_AFFILIATED_HOME_UNIVERSITY_VALUES if v is not None]
    rows = db.execute(
        select(College.home_university, func.count())
        .where(College.home_university.is_not(None), ~College.home_university.in_(excluded))
        .group_by(College.home_university)
        .order_by(College.home_university)
    ).all()
    return {"items": [{"name": name, "college_count": count} for name, count in rows]}


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
    name: str | None = None,
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
    if name:
        base_query = base_query.where(College.name.ilike(f"%{name}%"))
        count_query = count_query.where(College.name.ilike(f"%{name}%"))

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
    latest_year = _latest_data_year(db)

    # Figure out which quota/category/merit-exam slice of cutoff_history to compare
    # against, and which of the student's scores is the right one for that slice's
    # percentile scale. AI-quota rows are split by merit_exam (JEE vs MHT-CET vs NEET) -
    # mixing those would silently compare a score against the wrong exam's percentile
    # pool, so the quota+exam combination determines both the query filter and the score.
    if payload.student_type == "diploma":
        db_quota, category_filter, merit_exam_filter = "DIPLOMA", None, "DIPLOMA"
        score, score_label = payload.diploma_percentage or 0, "Diploma percentile"
    elif payload.quota == "AI":
        db_quota, category_filter = "AI", "AI"
        if payload.jee_percentile:
            merit_exam_filter, score, score_label = "JEE", payload.jee_percentile, "JEE percentile"
        elif payload.cet_percentile:
            merit_exam_filter, score, score_label = "MHT-CET", payload.cet_percentile, "CET percentile"
        else:
            merit_exam_filter, score, score_label = None, 0, "JEE or CET percentile"
    else:
        db_quota, merit_exam_filter = "MH", "MHT-CET"
        category_filter = CATEGORY_MAP.get(payload.category)
        if not category_filter:
            raise HTTPException(status_code=400, detail="Unsupported category.")
        score, score_label = payload.cet_percentile or payload.hsc_percentage or 0, "CET percentile"

    if score <= 0:
        raise HTTPException(status_code=400, detail=f"Please provide a valid {score_label}.")

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
        .where(CutoffHistory.quota == db_quota)
    )
    if db_quota == "MH":
        query = query.where(CutoffHistory.category == category_filter, CutoffHistory.level == "State Level")
    elif db_quota == "AI":
        query = query.where(CutoffHistory.category == category_filter, CutoffHistory.merit_exam == merit_exam_filter)
    else:
        query = query.where(CutoffHistory.level == "Diploma")

    branch_patterns = [f"%{b.strip()}%" for b in payload.preferred_branches if b.strip()]
    if branch_patterns:
        query = query.where(or_(*[Branch.course_name.ilike(p) for p in branch_patterns]))

    preferred_college_codes = [c.strip() for c in payload.preferred_colleges if c.strip()]
    if preferred_college_codes:
        query = query.where(Branch.institute_code.in_(preferred_college_codes))

    query = query.order_by(Branch.institute_code, Branch.choice_code, CutoffHistory.year.desc(), CutoffHistory.round.desc())

    rows = db.execute(query).all()

    grouped: dict[tuple[str, str], list] = {}
    for row in rows:
        grouped.setdefault((row.institute_code, row.choice_code), []).append(row)

    # Batch-fetch seat counts for every matched branch in one query instead of N+1.
    # Only meaningful for MH quota - seat_matrix doesn't break seats out by AI-quota category.
    seats_by_branch: dict[tuple[str, str], int] = {}
    if db_quota == "MH" and payload.category in SEAT_CATEGORY_MAP and grouped:
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

    # Home-University-aware comparison: a college's seats aren't just State Level - see
    # the module-level comment on LEVEL_HOME_TO_HOME for why. Batch-fetch the relevant
    # H/O-category rows for every matched branch in one query, then per-branch pick
    # whichever of {State Level, Home/Other-University level} gives the BEST (lowest)
    # cutoff for this student - that's their real best chance, not just the conservative
    # State-Level-only number.
    home_uni_best: dict[tuple[str, str], dict] = {}
    home_cat = CATEGORY_MAP_HOME.get(payload.category)
    other_cat = CATEGORY_MAP_OTHER.get(payload.category)
    if db_quota == "MH" and payload.home_university and home_cat and other_cat and grouped:
        keys = list(grouped.keys())
        ho_rows = db.execute(
            select(
                CutoffHistory.institute_code,
                CutoffHistory.choice_code,
                CutoffHistory.level,
                CutoffHistory.category,
                CutoffHistory.year,
                CutoffHistory.round,
                CutoffHistory.percentile,
            )
            .where(
                tuple_(CutoffHistory.institute_code, CutoffHistory.choice_code).in_(keys),
                CutoffHistory.quota == "MH",
                CutoffHistory.level.in_([LEVEL_HOME_TO_HOME, LEVEL_HOME_TO_OTHER, LEVEL_OTHER_TO_HOME, LEVEL_OTHER_TO_OTHER]),
                CutoffHistory.category.in_([home_cat, other_cat]),
            )
            .order_by(
                CutoffHistory.institute_code, CutoffHistory.choice_code, CutoffHistory.level,
                CutoffHistory.year.desc(), CutoffHistory.round.desc(),
            )
        ).all()
        ho_latest: dict[tuple[str, str, str], object] = {}
        for r in ho_rows:
            key = (r.institute_code, r.choice_code, r.level)
            ho_latest.setdefault(key, r)  # first row per group is latest, given the ORDER BY above

        for (institute_code, choice_code), group_rows in grouped.items():
            college_home_uni = group_rows[0].home_university
            if college_home_uni in NON_AFFILIATED_HOME_UNIVERSITY_VALUES:
                continue  # autonomous/deemed institutes have no H/O split to check
            is_home_match = college_home_uni == payload.home_university
            candidate_levels = (
                [LEVEL_HOME_TO_HOME, LEVEL_OTHER_TO_HOME] if is_home_match else [LEVEL_HOME_TO_OTHER, LEVEL_OTHER_TO_OTHER]
            )
            best_row = None
            for level_name in candidate_levels:
                row = ho_latest.get((institute_code, choice_code, level_name))
                if row and (best_row is None or row.percentile < best_row.percentile):
                    best_row = row
            if best_row:
                home_uni_best[(institute_code, choice_code)] = {
                    "percentile": best_row.percentile,
                    "level": best_row.level,
                    "year": best_row.year,
                    "round": best_row.round,
                }

    matches = []
    for (institute_code, choice_code), group_rows in grouped.items():
        latest = group_rows[0]  # rows are ordered year DESC, round DESC per group
        history = [{"year": r.year, "round": r.round, "percentile": round(r.percentile, 2), "level": "State Level"} for r in group_rows]

        # Prefer the Home/Other-University route if it's a genuinely better (lower) cutoff
        # than State Level for this student at this college.
        effective_percentile, effective_year, effective_round, effective_level = (
            latest.percentile, latest.year, latest.round, "State Level"
        )
        ho_best = home_uni_best.get((institute_code, choice_code))
        if ho_best and ho_best["percentile"] < effective_percentile:
            effective_percentile = ho_best["percentile"]
            effective_year, effective_round, effective_level = ho_best["year"], ho_best["round"], ho_best["level"]
            history.append({"year": ho_best["year"], "round": ho_best["round"], "percentile": round(ho_best["percentile"], 2), "level": ho_best["level"]})

        trend = "stable"
        distinct_years = sorted({r.year for r in group_rows}, reverse=True)
        if len(distinct_years) >= 2:
            prev_row = next((r for r in group_rows if r.year == distinct_years[1]), None)
            if prev_row:
                diff = latest.percentile - prev_row.percentile
                trend = "up" if diff > 0.5 else "down" if diff < -0.5 else "stable"

        chance = classify_score(score, effective_percentile)

        matches.append(
            {
                "id": f"{institute_code}-{choice_code}",
                "college_name": latest.college_name,
                "status": latest.status,
                "home_university": latest.home_university,
                "website": latest.official_website,
                "branch": latest.course_name,
                "category": payload.category if db_quota == "MH" else category_filter,
                "quota": db_quota,
                "merit_exam": merit_exam_filter,
                "cutoff": round(effective_percentile, 2),
                "cutoff_year": effective_year,
                "cutoff_round": effective_round,
                "cutoff_level": effective_level,
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
        "quota": db_quota,
        "merit_exam": merit_exam_filter,
        "score_used": round(score, 2),
        "score_label": score_label,
        "data_year": latest_year,
        "summary": summary,
        "colleges": matches[:10],
        "recommended": recommended,
    }
