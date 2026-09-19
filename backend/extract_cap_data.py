"""
Extract official MHT-CET CAP cutoff & seat-matrix data from the PDFs in
supabase_import/official_cap_<year>/ into normalized, Supabase-importable CSVs.

Replaces the old generate_official_cap_csv.py, which flattened each PDF into
one text blob and paired category codes with numbers positionally. That does
not work: these tables have multiple quota levels per branch (State Level,
Home-University-to-Home, Home-University-to-Other, Other-to-Other,
Other-to-Home, All-India) each with multiple stage rows (I, II, ...) that are
frequently SPARSE (a category column is blank once its seats run out). This
script instead uses pdfplumber's ruled-table extraction (page.find_tables()),
which reproduces the real grid including blank cells, and anchors each table
to the nearest preceding institute/branch/level heading using word positions.

Two cutoff layouts are handled:
  - "MH" layout (regular Maharashtra-quota cutoff PDFs): one bordered table
    per (branch, quota-level) with a category header row and 1+ stage rows.
  - "simple" layout (All-India-quota and Diploma cutoff PDFs): one bordered
    table per file with one row per (institute, branch) and a single merit
    rank+percentile column.

Seat-matrix PDFs get their own parser (one bordered table per branch with a
category x gender seat grid, plus PWD/DEF/EWS/TFWS reserved-seat rows).

Usage:
    .venv/Scripts/python.exe extract_cap_data.py [--years 2023,2024,2026] [--workers 6]

Output (under supabase_import/):
    colleges.csv        institute_code, name, status, home_university
    branches.csv        institute_code, choice_code, course_name
    cutoff_history.csv  institute_code, choice_code, year, round, quota, level, stage, category, merit_rank, percentile, source_pdf
    seat_matrix.csv      institute_code, choice_code, year, round, category, gender, seats, source_pdf
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pdfplumber

BASE = Path(__file__).resolve().parent
IMPORT_DIR = BASE / "supabase_import"

INSTITUTE_RE = re.compile(r"^(\d{4,5})\s*-\s*(.+)$")
# Choice codes can carry a trailing letter suffix - one letter ("303319113K" = a
# Konkan-quota variant of branch 303319110, per the legend's "K-Konkan Seats") or two
# ("303337293LK" = Ladies + Konkan combined) - each a DIFFERENT branch, not a typo.
# Matching digits-only here silently merged that table's rows into whichever branch
# came before it - see the 2023ENGG_CAP1_CutOff.pdf institute 3033 case.
BRANCH_RE = re.compile(r"^(\d{6,}[A-Z]*)\s*-\s*(.+)$")
STATUS_RE = re.compile(r"^Status\s*:\s*(.+?)(?:\s*Home University\s*:\s*(.+))?$")
RANK_PCT_RE = re.compile(r"^([\d,]+)\s*\(([\d.]+)\)$")
NOISE_SNIPPETS = (
    "legends:",
    # NOT "maharashtra state seats" alone - a real level heading, "Maharashtra State
    # Seats Allotted to All India Candidature Candidates", shares that prefix with the
    # page footer ("Maharashtra State Seats - Cut Off Indicates..."). Match the footer's
    # more specific phrase instead so the real heading survives.
    "cut off indicates",
    "published date",
    "state cet cell",
    "f:only for female",
    "page ",
)
LEVEL_HINTS = ("level", "seats allotted", "candidates", "all india", "university")


def norm_institute(code: str) -> str:
    """2023 PDFs use unpadded institute codes ('1002'); 2024/2026 use 5-digit ('01002').
    Normalize to 5 digits everywhere so the same college joins across years."""
    return code.strip().zfill(5)


def norm_choice(code: str) -> str:
    """Same padding issue for branch/choice codes (9 vs 10 digits), plus some codes
    carry a trailing letter (e.g. '303319113K' for a Konkan-quota variant) - pad the
    numeric part to 10 digits and keep the letter suffix, rather than zfill-ing the
    whole string (which would leave a 10-char letter-suffixed code unpadded)."""
    code = code.strip()
    m = re.match(r"^(\d+)([A-Za-z]*)$", code)
    if m:
        digits, suffix = m.groups()
        return digits.zfill(10) + suffix
    return code.zfill(10)


def round_and_quota_from_name(name: str) -> tuple[str, str]:
    upper = name.upper()
    if "CAP1" in upper:
        round_name = "CAP1"
    elif "CAP2" in upper:
        round_name = "CAP2"
    elif "CAP3" in upper:
        round_name = "CAP3"
    elif "CAP4" in upper:
        round_name = "CAP4"
    else:
        round_name = "SEAT_MATRIX"

    if "_AI_" in upper or upper.endswith("AI_CUTOFF.PDF"):
        quota = "AI"
    elif "DIPLOMA" in upper:
        quota = "DIPLOMA"
    elif "MH" in upper or "CUTOFF" in upper:
        quota = "MH"
    else:
        quota = "UNKNOWN"
    return round_name, quota


def is_noise_line(text: str) -> bool:
    low = text.lower().strip()
    if not low:
        return True
    if low.isdigit():
        return True
    return any(snippet in low for snippet in NOISE_SNIPPETS)


def looks_like_level(text: str) -> bool:
    low = text.lower()
    return any(hint in low for hint in LEVEL_HINTS)


def lines_outside_tables(page, tables) -> list[tuple[float, str]]:
    """Group words that fall outside any ruled table into text lines, ordered top-to-bottom."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    boxes = [t.bbox for t in tables]

    def in_table(w) -> bool:
        cy = (w["top"] + w["bottom"]) / 2
        cx = (w["x0"] + w["x1"]) / 2
        for (x0, top, x1, bottom) in boxes:
            if x0 - 2 <= cx <= x1 + 2 and top - 2 <= cy <= bottom + 2:
                return True
        return False

    filtered = [w for w in words if not in_table(w)]
    filtered.sort(key=lambda w: (round(w["top"]), w["x0"]))

    lines: list[tuple[float, list]] = []
    cur_top = None
    cur_words: list = []
    for w in filtered:
        t = w["top"]
        if cur_top is None or abs(t - cur_top) <= 3:
            cur_words.append(w)
            cur_top = t if cur_top is None else min(cur_top, t)
        else:
            lines.append((cur_top, cur_words))
            cur_words = [w]
            cur_top = t
    if cur_words:
        lines.append((cur_top, cur_words))

    out = []
    for top, ws in lines:
        ws_sorted = sorted(ws, key=lambda x: x["x0"])
        text = " ".join(x["text"] for x in ws_sorted)
        out.append((top, text))
    out.sort(key=lambda x: x[0])
    return out


def clean_cell_number(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def parse_mh_cutoff_pdf(path: Path, year: str, round_name: str, quota: str):
    college_rows: dict[str, dict] = {}
    branch_rows: dict[tuple[str, str], dict] = {}
    cutoff_rows: list[dict] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.find_tables()
            except Exception:
                tables = []
            text_lines = lines_outside_tables(page, tables)

            events: list[tuple[float, str, object]] = [(top, "line", txt) for top, txt in text_lines]
            events += [(t.bbox[1], "table", t) for t in tables]
            events.sort(key=lambda e: e[0])

            institute_code = None
            institute_name = None
            choice_code = None
            course_name = None
            status_text = None
            home_university = None
            pending_level = None
            awaiting = None  # "institute" | "branch" | None

            for _, kind, payload in events:
                if kind == "line":
                    text = re.sub(r"\s+", " ", str(payload)).strip()
                    if not text:
                        continue

                    m = INSTITUTE_RE.match(text)
                    if m:
                        institute_code, institute_name = norm_institute(m.group(1)), m.group(2).strip()
                        choice_code = None
                        course_name = None
                        status_text = None
                        home_university = None
                        pending_level = None
                        awaiting = "institute"
                        continue

                    m = BRANCH_RE.match(text)
                    if m:
                        choice_code, course_name = norm_choice(m.group(1)), m.group(2).strip()
                        status_text = None
                        home_university = None
                        pending_level = None
                        awaiting = "branch"
                        continue

                    m = STATUS_RE.match(text)
                    if m:
                        status_text = m.group(1).strip() if m.group(1) else None
                        home_university = m.group(2).strip() if m.group(2) else None
                        awaiting = None
                        continue

                    if is_noise_line(text):
                        continue

                    if awaiting == "institute" and institute_name is not None:
                        institute_name = f"{institute_name} {text}".strip()
                        continue

                    if awaiting == "branch" and course_name is not None and not looks_like_level(text):
                        course_name = f"{course_name} {text}".strip()
                        continue

                    pending_level = text
                    awaiting = None
                    continue

                # kind == "table"
                if not institute_code or not choice_code:
                    continue
                grid = payload.extract()
                if not grid or len(grid) < 2:
                    continue
                header = grid[0]
                categories = [clean_cell_number(c) for c in header[1:]]
                level_name = pending_level or "State Level"

                college_rows[institute_code] = {
                    "institute_code": institute_code,
                    "name": institute_name or "",
                    "status": status_text or "",
                    "home_university": home_university or "",
                }
                branch_rows[(institute_code, choice_code)] = {
                    "institute_code": institute_code,
                    "choice_code": choice_code,
                    "course_name": course_name or "",
                }

                for data_row in grid[1:]:
                    if not data_row:
                        continue
                    stage = clean_cell_number(data_row[0]) or "I"
                    for idx, cell in enumerate(data_row[1:]):
                        if idx >= len(categories):
                            break
                        cell_text = clean_cell_number(cell)
                        if not cell_text:
                            continue
                        rm = RANK_PCT_RE.match(cell_text)
                        if not rm:
                            continue
                        category = categories[idx]
                        if not category:
                            continue
                        cutoff_rows.append(
                            {
                                "institute_code": institute_code,
                                "choice_code": choice_code,
                                "year": year,
                                "round": round_name,
                                "quota": quota,
                                "level": level_name,
                                "stage": stage,
                                "category": category,
                                "merit_rank": rm.group(1).replace(",", ""),
                                "percentile": rm.group(2),
                                "source_pdf": path.name,
                            }
                        )
                pending_level = None

    return list(college_rows.values()), list(branch_rows.values()), cutoff_rows


def parse_simple_cutoff_pdf(path: Path, year: str, round_name: str, quota: str):
    college_rows: dict[str, dict] = {}
    branch_rows: dict[tuple[str, str], dict] = {}
    cutoff_rows: list[dict] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.find_tables()
            except Exception:
                tables = []
            for t in tables:
                grid = t.extract()
                if not grid:
                    continue
                for row in grid[1:]:
                    if not row or len(row) < 4:
                        continue
                    sr = clean_cell_number(row[0])
                    if not sr or not sr.isdigit():
                        continue
                    merit_cell = clean_cell_number(row[1])
                    choice_code_raw = clean_cell_number(row[2])
                    institute_cell = clean_cell_number(row[3])
                    course_name = clean_cell_number(row[4]) if len(row) > 4 else ""
                    seat_type = clean_cell_number(row[-1]) if len(row) > 5 else quota

                    rm = RANK_PCT_RE.match(merit_cell)
                    im = INSTITUTE_RE.match(institute_cell)
                    if not rm or not im or not choice_code_raw.isdigit():
                        continue
                    choice_code = norm_choice(choice_code_raw)
                    institute_code, institute_name = norm_institute(im.group(1)), im.group(2).strip()

                    college_rows.setdefault(
                        institute_code,
                        {"institute_code": institute_code, "name": institute_name, "status": "", "home_university": ""},
                    )
                    branch_rows.setdefault(
                        (institute_code, choice_code),
                        {"institute_code": institute_code, "choice_code": choice_code, "course_name": course_name},
                    )
                    cutoff_rows.append(
                        {
                            "institute_code": institute_code,
                            "choice_code": choice_code,
                            "year": year,
                            "round": round_name,
                            "quota": quota,
                            "level": "All India" if quota == "AI" else "Diploma",
                            "stage": "I",
                            "category": seat_type or quota,
                            "merit_rank": rm.group(1).replace(",", ""),
                            "percentile": rm.group(2),
                            "source_pdf": path.name,
                        }
                    )
    return list(college_rows.values()), list(branch_rows.values()), cutoff_rows


SEAT_CATEGORY_HEADER = ("OPEN", "SC", "ST", "VJ/DT", "NTB", "NTC", "NTD", "OBC", "SEBC")


def parse_seat_matrix_pdf(path: Path, year: str):
    college_rows: dict[str, dict] = {}
    branch_rows: dict[tuple[str, str], dict] = {}
    seat_rows: list[dict] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.find_tables()
            except Exception:
                tables = []
            text_lines = lines_outside_tables(page, tables)
            institute_code = institute_name = status_text = None
            for _, txt in text_lines:
                text = re.sub(r"\s+", " ", txt).strip()
                m = INSTITUTE_RE.match(text)
                if m:
                    institute_code, institute_name = norm_institute(m.group(1)), m.group(2).strip()

            for t in tables:
                grid = t.extract()
                if not grid or len(grid) < 6:
                    continue

                inst_code, inst_name, choice_code, course_name, cap_seats = (
                    institute_code,
                    institute_name,
                    None,
                    None,
                    None,
                )
                status_row_idx = None
                choice_row_idx = None
                for i, row in enumerate(grid[:8]):
                    if row and row[0]:
                        cell = clean_cell_number(row[0])
                        im = INSTITUTE_RE.match(cell)
                        if im:
                            inst_code, inst_name = norm_institute(im.group(1)), im.group(2).strip()
                        if "CAP Seats" in " ".join(str(c) for c in row if c):
                            status_row_idx = i
                        # Choice code / course name sit in separate cells on their own row:
                        # ['0100219110', 'Civil Engineering', None, ...] - code can carry
                        # a trailing letter (e.g. Konkan-quota 'K' variant), same as BRANCH_RE.
                        if choice_row_idx is None and re.match(r"^\d{6,}[A-Z]*$", cell):
                            choice_row_idx = i
                            choice_code = norm_choice(cell)
                            course_name = clean_cell_number(row[1]) if len(row) > 1 else ""

                if not inst_code or not choice_code:
                    continue

                status_text = None
                if status_row_idx is not None:
                    status_text = clean_cell_number(grid[status_row_idx][0])

                college_rows.setdefault(
                    inst_code, {"institute_code": inst_code, "name": inst_name or "", "status": status_text or "", "home_university": ""}
                )
                branch_rows.setdefault(
                    (inst_code, choice_code),
                    {"institute_code": inst_code, "choice_code": choice_code, "course_name": course_name or ""},
                )

                header_idx = None
                genderrow_idx = None
                for i, row in enumerate(grid):
                    if row and clean_cell_number(row[0]) == "Category":
                        header_idx = i
                    if row and clean_cell_number(row[0]) == "General / Ladies":
                        genderrow_idx = i
                if header_idx is None:
                    continue

                cat_header = grid[header_idx]
                categories_by_col: dict[int, str] = {}
                current_cat = None
                for col_idx, cell in enumerate(cat_header[1:], start=1):
                    val = clean_cell_number(cell)
                    if val:
                        current_cat = val
                    if current_cat:
                        categories_by_col[col_idx] = current_cat

                gender_by_col: dict[int, str] = {}
                if genderrow_idx is not None:
                    for col_idx, cell in enumerate(grid[genderrow_idx][1:], start=1):
                        val = clean_cell_number(cell)
                        if val:
                            gender_by_col[col_idx] = val

                data_start = (genderrow_idx or header_idx) + 1
                for row in grid[data_start:]:
                    if not row or not row[0]:
                        continue
                    row_label = clean_cell_number(row[0])
                    row_text = " ".join(clean_cell_number(c) for c in row if c)
                    if not row_label or "Common Reserved" in row_label or "Tution Fee" in row_text or "Economically" in row_text:
                        # still capture EWS/TFWS totals as standalone rows; these live in whichever
                        # cell the "Seats: N" text happens to be, not necessarily column 0
                        ews_m = re.search(r"Economically Weaker Section \(EWS\) Seats:\s*(\d+)", row_text)
                        if ews_m:
                            seat_rows.append(
                                {
                                    "institute_code": inst_code,
                                    "choice_code": choice_code,
                                    "year": year,
                                    "level": "Reservation",
                                    "category": "EWS",
                                    "gender": "TOTAL",
                                    "seats": ews_m.group(1),
                                    "source_pdf": path.name,
                                }
                            )
                        tfws_m = re.search(r"Tution Fee Waiver Scheme.*?Seats:\s*(\d+)", row_text)
                        if tfws_m:
                            seat_rows.append(
                                {
                                    "institute_code": inst_code,
                                    "choice_code": choice_code,
                                    "year": year,
                                    "level": "Reservation",
                                    "category": "TFWS",
                                    "gender": "TOTAL",
                                    "seats": tfws_m.group(1),
                                    "source_pdf": path.name,
                                }
                            )
                        continue
                    if row_label not in ("State Level", "PWD", "DEF") and not row_label.startswith("PWD") and not row_label.startswith("DEF"):
                        continue
                    for col_idx, cell in enumerate(row[1:], start=1):
                        val = clean_cell_number(cell)
                        if not val or not val.replace(",", "").isdigit():
                            continue
                        category = categories_by_col.get(col_idx, "TOTAL" if col_idx == len(row) - 1 else "")
                        gender = gender_by_col.get(col_idx, "")
                        seat_rows.append(
                            {
                                "institute_code": inst_code,
                                "choice_code": choice_code,
                                "year": year,
                                "level": row_label,
                                "category": category,
                                "gender": gender,
                                "seats": val.replace(",", ""),
                                "source_pdf": path.name,
                            }
                        )

    return list(college_rows.values()), list(branch_rows.values()), seat_rows


PARTS_DIR = IMPORT_DIR / "_parts"
COLLEGE_FIELDS = ["institute_code", "name", "status", "home_university"]
BRANCH_FIELDS = ["institute_code", "choice_code", "course_name"]
CUTOFF_FIELDS = ["institute_code", "choice_code", "year", "round", "quota", "level", "stage", "category", "merit_rank", "percentile", "source_pdf"]
SEAT_FIELDS = ["institute_code", "choice_code", "year", "level", "category", "gender", "seats", "source_pdf"]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def part_paths(stem: str) -> tuple[Path, Path, Path]:
    d = PARTS_DIR / stem
    return d / "colleges.csv", d / "branches.csv", d / "rows.csv"


def part_done_marker(stem: str) -> Path:
    return PARTS_DIR / stem / "_DONE"


def process_cutoff_file(path_str: str, year: str):
    path = Path(path_str)
    stem = f"cutoff_{year}_{path.stem}"
    done = part_done_marker(stem)
    college_p, branch_p, rows_p = part_paths(stem)
    if done.exists():
        print(f"[skip] {path.name} already done (checkpoint found)", flush=True)
        return [f"{stem}"], "cutoff", []

    round_name, quota = round_and_quota_from_name(path.name)
    try:
        if quota in ("AI", "DIPLOMA"):
            colleges, branches, cutoffs = parse_simple_cutoff_pdf(path, year, round_name, quota)
        else:
            colleges, branches, cutoffs = parse_mh_cutoff_pdf(path, year, round_name, quota)
        write_csv(college_p, COLLEGE_FIELDS, colleges)
        write_csv(branch_p, BRANCH_FIELDS, branches)
        write_csv(rows_p, CUTOFF_FIELDS, cutoffs)
        done.write_text("ok")
        print(f"[ok] {path.name}: {len(colleges)} colleges, {len(branches)} branches, {len(cutoffs)} cutoff rows", flush=True)
        return [stem], "cutoff", []
    except Exception as exc:  # pragma: no cover
        tb = traceback.format_exc()
        print(f"[FAIL] {path.name}: {exc}\n{tb}", flush=True)
        return [], "cutoff", [f"{path.name}: {exc}"]


def process_seat_matrix_file(path_str: str, year: str):
    path = Path(path_str)
    stem = f"seatmatrix_{year}_{path.stem}"
    done = part_done_marker(stem)
    college_p, branch_p, rows_p = part_paths(stem)
    if done.exists():
        print(f"[skip] {path.name} already done (checkpoint found)", flush=True)
        return [stem], "seat", []

    try:
        colleges, branches, seats = parse_seat_matrix_pdf(path, year)
        write_csv(college_p, COLLEGE_FIELDS, colleges)
        write_csv(branch_p, BRANCH_FIELDS, branches)
        write_csv(rows_p, SEAT_FIELDS, seats)
        done.write_text("ok")
        print(f"[ok] {path.name}: {len(colleges)} colleges, {len(branches)} branches, {len(seats)} seat rows", flush=True)
        return [stem], "seat", []
    except Exception as exc:  # pragma: no cover
        tb = traceback.format_exc()
        print(f"[FAIL] {path.name}: {exc}\n{tb}", flush=True)
        return [], "seat", [f"{path.name}: {exc}"]


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _more_complete(existing: dict | None, candidate: dict, fields: list[str]) -> dict:
    """Prefer whichever record has more non-blank values among `fields`, instead of
    blindly keeping whichever checkpoint happened to merge first. The same institute
    or branch can appear in multiple source files (e.g. both an AI-quota and an
    MH-quota cutoff PDF) with different completeness - e.g. institute 06006 choice
    0600619110's course_name came back empty from the AI file's simpler parser but
    "Civil Engineering" from the MH file; alphabetical-stem-order merging picked the
    AI file's blank value. Score-and-prefer avoids depending on merge order."""
    if existing is None:
        return candidate
    existing_score = sum(1 for f in fields if existing.get(f, "").strip())
    candidate_score = sum(1 for f in fields if candidate.get(f, "").strip())
    return candidate if candidate_score > existing_score else existing


def merge_parts():
    """Concatenate every completed per-file checkpoint under _parts/ into the final CSVs.
    Safe to call any time (mid-run or after) - only reads what's already finished."""
    all_colleges: dict[str, dict] = {}
    all_branches: dict[tuple[str, str], dict] = {}
    all_cutoffs: list[dict] = []
    all_seats: list[dict] = []

    if not PARTS_DIR.exists():
        print("No _parts/ checkpoints found yet.")
        return

    stems = sorted(p.name for p in PARTS_DIR.iterdir() if p.is_dir() and part_done_marker(p.name).exists())
    print(f"Merging {len(stems)} completed checkpoints...")
    for stem in stems:
        college_p, branch_p, rows_p = part_paths(stem)
        for c in read_csv_rows(college_p):
            key = c["institute_code"]
            all_colleges[key] = _more_complete(all_colleges.get(key), c, ["name", "status", "home_university"])
        for b in read_csv_rows(branch_p):
            key = (b["institute_code"], b["choice_code"])
            all_branches[key] = _more_complete(all_branches.get(key), b, ["course_name"])
        rows = read_csv_rows(rows_p)
        if stem.startswith("cutoff_"):
            all_cutoffs.extend(rows)
        else:
            all_seats.extend(rows)

    write_csv(IMPORT_DIR / "colleges.csv", COLLEGE_FIELDS, list(all_colleges.values()))
    write_csv(IMPORT_DIR / "branches.csv", BRANCH_FIELDS, list(all_branches.values()))
    write_csv(IMPORT_DIR / "cutoff_history.csv", CUTOFF_FIELDS, all_cutoffs)
    write_csv(IMPORT_DIR / "seat_matrix.csv", SEAT_FIELDS, all_seats)

    print("\n=== MERGE SUMMARY ===")
    print(f"checkpoints merged: {len(stems)}")
    print(f"colleges: {len(all_colleges)}")
    print(f"branches: {len(all_branches)}")
    print(f"cutoff_history rows: {len(all_cutoffs)}")
    print(f"seat_matrix rows: {len(all_seats)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2023,2024,2026")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--merge-only", action="store_true", help="Skip parsing, just merge existing _parts/ checkpoints")
    parser.add_argument("--list", action="store_true", help="List all jobs with done/pending status and exit")
    parser.add_argument("--file", help="Process exactly this one PDF, single-threaded, then exit (light on resources)")
    parser.add_argument("--year", help="Year for --file (required if --file is given)")
    args = parser.parse_args()

    if args.merge_only:
        merge_parts()
        return

    years = args.years.split(",")

    if args.list:
        year_dirs = {
            "2023": IMPORT_DIR / "official_cap_2023",
            "2024": IMPORT_DIR / "official_cap_2024",
            "2026": IMPORT_DIR / "official_cap_2026",
        }
        for year in years:
            for pdf_path in sorted(year_dirs[year].glob("*.pdf")):
                name_up = pdf_path.name.upper()
                kind = "seat" if "SEATMATRIX" in name_up else "cutoff"
                stem = f"{kind}matrix_{year}_{pdf_path.stem}" if kind == "seat" else f"cutoff_{year}_{pdf_path.stem}"
                status = "DONE" if part_done_marker(stem).exists() else "pending"
                print(f"[{status:7}] {year}  {pdf_path.name}")
        return

    if args.file:
        if not args.year:
            print("--year is required with --file")
            sys.exit(1)
        path = Path(args.file)
        name_up = path.name.upper()
        if "SEATMATRIX" in name_up:
            _stems, _kind, errs = process_seat_matrix_file(str(path), args.year)
        else:
            _stems, _kind, errs = process_cutoff_file(str(path), args.year)
        if errs:
            print("ERRORS:", errs)
            sys.exit(1)
        print("Done. Run with --merge-only to fold this into the final CSVs.")
        return
    year_dirs = {
        "2023": IMPORT_DIR / "official_cap_2023",
        "2024": IMPORT_DIR / "official_cap_2024",
        "2026": IMPORT_DIR / "official_cap_2026",
    }

    cutoff_jobs = []
    seatmatrix_jobs = []
    for year in years:
        d = year_dirs[year]
        for pdf_path in sorted(d.glob("*.pdf")):
            name_up = pdf_path.name.upper()
            if "SEATMATRIX" in name_up:
                seatmatrix_jobs.append((str(pdf_path), year))
            elif "CUTOFF" in name_up or "CUT" in name_up:
                cutoff_jobs.append((str(pdf_path), year))

    errors: list[str] = []
    total_jobs = len(cutoff_jobs) + len(seatmatrix_jobs)
    done_count = 0

    print(f"Processing {len(cutoff_jobs)} cutoff PDFs + {len(seatmatrix_jobs)} seat-matrix PDFs "
          f"with {args.workers} workers (checkpointed under _parts/, resumable)...", flush=True)

    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_cutoff_file, p, y): p for p, y in cutoff_jobs}
        futures.update({ex.submit(process_seat_matrix_file, p, y): p for p, y in seatmatrix_jobs})
        for fut in as_completed(futures):
            _stems, _kind, errs = fut.result()
            errors.extend(errs)
            done_count += 1
            print(f"--- progress: {done_count}/{total_jobs} files done ---", flush=True)

    print("\nAll files processed (or skipped via checkpoint). Merging...", flush=True)
    merge_parts()

    if errors:
        print(f"\n{len(errors)} file(s) failed:")
        for e in errors[:50]:
            print(" -", e)


if __name__ == "__main__":
    main()
