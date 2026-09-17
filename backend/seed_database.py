import json
from pathlib import Path

from sqlalchemy import create_engine

from database import DATABASE_URL
from models import Base, College, Branch, CutoffHistory

DATA_FILE = Path(__file__).resolve().parent / "college_data.json"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)

with DATA_FILE.open("r", encoding="utf-8") as f:
    colleges = json.load(f)

with engine.begin() as conn:
    for college in colleges:
        college_id = college["id"]
        college_record = {
            "id": college_id,
            "name": college["name"],
            "city": college["city"],
            "district": college["district"],
            "college_type": college["college_type"],
            "official_website": college.get("official_website"),
            "total_seats": college.get("total_seats", 0),
            "average_cutoff": college.get("average_cutoff", 0),
        }

        if conn.execute(
            College.__table__.select().where(College.id == college_id)
        ).first() is None:
            conn.execute(College.__table__.insert(), [college_record])

        for branch_name in college.get("branches", []):
            branch_payload = {
                "college_id": college_id,
                "branch_name": branch_name,
                "intake": 60,
                "placement_signal": "strong",
            }
            conn.execute(Branch.__table__.insert().values(**branch_payload))

        for cutoff in college.get("cutoff_history", []):
            cutoff_payload = {
                "college_id": college_id,
                "branch_name": cutoff.get("branch", "General"),
                "category": cutoff.get("category", "GOPEN"),
                "year": cutoff.get("year", 2025),
                "cutoff_percent": float(cutoff.get("cutoff", 0)),
                "closing_rank": cutoff.get("closing_rank"),
                "trend_note": cutoff.get("trend", "stable"),
            }
            conn.execute(CutoffHistory.__table__.insert().values(**cutoff_payload))

print(f"Seeded {len(colleges)} colleges into PostgreSQL.")
