from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "college_data.json"

app = FastAPI(
    title="Maharashtra Engineering Admission Predictor API",
    version="1.0.0",
    description="Production-ready admissions and cutoff prediction API for Maharashtra engineering students.",
)

allowed_origins = (
    os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
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

request_log: dict[str, list[float]] = defaultdict(list)


def load_college_data() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


COLLEGE_DATA = load_college_data()


class StudentProfile(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=255)
    student_type: Literal["12th", "diploma"] = "12th"
    city: str = Field(default="Pune", max_length=80)
    domicile: Literal["Maharashtra", "Non-Maharashtra"] = "Maharashtra"
    hsc_percentage: float | None = Field(default=None, ge=40, le=100)
    cet_score: float | None = Field(default=None, ge=0, le=200)
    jee_score: float | None = Field(default=None, ge=0, le=400)
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
def dashboard_summary() -> dict:
    total_colleges = len(COLLEGE_DATA)
    top_colleges = [college for college in COLLEGE_DATA if college.get("average_cutoff", 0) >= 85]
    return {
        "total_colleges": total_colleges,
        "total_branches": len({branch for college in COLLEGE_DATA for branch in college.get("branches", [])}),
        "top_colleges": len(top_colleges),
        "districts": len({college["district"] for college in COLLEGE_DATA}),
        "sample_trends": [
            {"name": "Pune", "value": 32},
            {"name": "Mumbai", "value": 22},
            {"name": "Nagpur", "value": 18},
            {"name": "Nashik", "value": 14},
        ],
    }


@app.get("/colleges")
def get_colleges(
    category: str | None = None,
    city: str | None = None,
    branch: str | None = None,
    limit: int = 20,
):
    items = COLLEGE_DATA
    if category:
        items = [college for college in items if category in college.get("cutoff_history", [{}])[0].get("categories", [])]
    if city:
        items = [college for college in items if college.get("city", "").lower() == city.lower()]
    if branch:
        items = [college for college in items if any(branch.lower() in b.lower() for b in college.get("branches", []))]

    results = []
    for college in items[:limit]:
        cutoff_entry = college.get("cutoff_history", [{}])
        latest_cutoff = cutoff_entry[-1] if cutoff_entry else {}
        results.append(
            {
                "id": college["id"],
                "name": college["name"],
                "city": college["city"],
                "district": college["district"],
                "type": college["college_type"],
                "website": college["official_website"],
                "average_cutoff": college.get("average_cutoff", 0),
                "seats": college.get("total_seats", 0),
                "branches": college.get("branches", []),
                "latest_cutoff": latest_cutoff.get("cutoff", 0),
            }
        )

    return {"count": len(results), "items": results}


@app.get("/colleges/{college_id}")
def get_college(college_id: str):
    for college in COLLEGE_DATA:
        if college["id"] == college_id:
            return college
    raise HTTPException(status_code=404, detail="College not found")


@app.post("/predict")
def predict_colleges(payload: StudentProfile):
    if payload.student_type == "12th":
        score = payload.hsc_percentage or payload.cet_score or 0
    else:
        score = payload.diploma_percentage or 0

    if score <= 0:
        raise HTTPException(status_code=400, detail="Please provide a valid academic score.")

    preferred_branches = [branch.lower() for branch in payload.preferred_branches]
    matches = []
    for college in COLLEGE_DATA:
        if payload.category not in [
            item.get("category") for item in college.get("cutoff_history", [])
        ]:
            continue

        if preferred_branches and not any(
            branch.lower() in college.get("branches", [])
            for branch in preferred_branches
        ):
            branch_match = False
            for branch in college.get("branches", []):
                if any(item.lower() in branch.lower() for item in preferred_branches):
                    branch_match = True
                    break
            if not branch_match:
                continue

        latest_cutoff = None
        for item in college.get("cutoff_history", []):
            if item.get("category") == payload.category:
                latest_cutoff = item
                break

        if latest_cutoff is None:
            continue

        cutoff = float(latest_cutoff.get("cutoff", 0))
        chance = classify_score(score, cutoff)
        matches.append(
            {
                "id": college["id"],
                "college_name": college["name"],
                "city": college["city"],
                "district": college["district"],
                "branch": latest_cutoff.get("branch", "General"),
                "category": payload.category,
                "cutoff": cutoff,
                "your_score": round(score, 2),
                "chance": chance,
                "trend": latest_cutoff.get("trend", "stable"),
                "college_type": college["college_type"],
                "website": college["official_website"],
                "cutoff_history": college.get("cutoff_history", []),
            }
        )

    matches.sort(key=lambda item: (item["cutoff"], item["college_name"]))

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
        "summary": summary,
        "colleges": matches[:10],
        "recommended": recommended,
    }
