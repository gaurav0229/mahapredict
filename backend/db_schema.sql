-- Maharashtra Engineering Admission Predictor — schema for real CAP data.
--
-- Replaces the earlier placeholder schema (which was never wired up to the
-- API and didn't match the shape of the official cutoff/seat-matrix PDFs).
-- Source data is extracted by backend/extract_cap_data.py from the official
-- MHT-CET CAP cutoff and seat-matrix PDFs in backend/supabase_import/, and
-- imported from supabase_import/colleges.csv, branches.csv,
-- cutoff_history.csv and seat_matrix.csv.
--
-- Key facts baked into this shape (see extract_cap_data.py's module
-- docstring for the full reasoning):
--   * A branch's cutoff isn't one number — it's split by quota (MH / AI /
--     DIPLOMA), by level (State Level, Home-University-to-Home,
--     Home-University-to-Other, Other-to-Other, Other-to-Home, All India),
--     and by stage (I, II, ...) within a single CAP round, each with its
--     own per-category rank + percentile.
--   * Seats are likewise split by category x gender (G/L), with separate
--     PWD / DEF / EWS / TFWS reservations layered on top.
--   * institute_code / choice_code are zero-padded (5 / 10 digits) — the
--     2023 PDFs omit leading zeros, so the extractor normalizes them; do
--     the same for any other data you load by hand.

CREATE TABLE IF NOT EXISTS colleges (
    institute_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(120),              -- e.g. "Government Autonomous", "Un-Aided Autonomous"
    home_university VARCHAR(255),     -- e.g. "Sant Gadge Baba Amravati University"
    city VARCHAR(120),                -- not present in CAP PDFs; enrich separately
    district VARCHAR(120),            -- not present in CAP PDFs; enrich separately
    official_website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    institute_code VARCHAR(10) NOT NULL REFERENCES colleges(institute_code) ON DELETE CASCADE,
    choice_code VARCHAR(12) NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    PRIMARY KEY (institute_code, choice_code)
);

CREATE TABLE IF NOT EXISTS cutoff_history (
    id BIGSERIAL PRIMARY KEY,
    institute_code VARCHAR(10) NOT NULL,
    choice_code VARCHAR(12) NOT NULL,
    year INTEGER NOT NULL,
    round VARCHAR(20) NOT NULL,           -- CAP1 / CAP2 / CAP3 / CAP4
    quota VARCHAR(20) NOT NULL,           -- MH / AI / DIPLOMA
    level VARCHAR(120) NOT NULL,          -- e.g. "State Level", "All India"
    stage VARCHAR(30) NOT NULL,           -- I / II / ... - some legacy-template PDFs (e.g.
                                           -- 2023 CAP3) use compound labels like "I-Non Defence"
    category VARCHAR(30) NOT NULL,        -- e.g. GOPENS, LOBCH, GOPENO, EWS, TFWS, AI
    merit_rank INTEGER NOT NULL,
    percentile DOUBLE PRECISION NOT NULL,
    source_pdf VARCHAR(120),
    FOREIGN KEY (institute_code, choice_code) REFERENCES branches(institute_code, choice_code) ON DELETE CASCADE,
    UNIQUE (institute_code, choice_code, year, round, quota, level, stage, category)
);

CREATE TABLE IF NOT EXISTS seat_matrix (
    id BIGSERIAL PRIMARY KEY,
    institute_code VARCHAR(10) NOT NULL,
    choice_code VARCHAR(12) NOT NULL,
    year INTEGER NOT NULL,
    level VARCHAR(30) NOT NULL,           -- State Level / PWD / DEF / (blank = EWS/TFWS totals)
    category VARCHAR(30) NOT NULL,        -- OPEN / SC / ST / VJ/DT / NTB / NTC / NTD / OBC / SEBC / Total / EWS / TFWS
    gender VARCHAR(10) NOT NULL,          -- G / L / TOTAL / "G + L"
    seats INTEGER NOT NULL,
    source_pdf VARCHAR(120),
    FOREIGN KEY (institute_code, choice_code) REFERENCES branches(institute_code, choice_code) ON DELETE CASCADE,
    UNIQUE (institute_code, choice_code, year, level, category, gender)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    percentile DOUBLE PRECISION NOT NULL,
    category VARCHAR(30) NOT NULL,
    preferred_branches TEXT NOT NULL,
    recommendation_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_branches_course_name ON branches(course_name);
CREATE INDEX IF NOT EXISTS idx_cutoff_institute ON cutoff_history(institute_code);
CREATE INDEX IF NOT EXISTS idx_cutoff_choice ON cutoff_history(choice_code);
CREATE INDEX IF NOT EXISTS idx_cutoff_category_year ON cutoff_history(category, year);
CREATE INDEX IF NOT EXISTS idx_cutoff_lookup ON cutoff_history(year, round, quota, category);
CREATE INDEX IF NOT EXISTS idx_seat_institute ON seat_matrix(institute_code);
CREATE INDEX IF NOT EXISTS idx_seat_choice ON seat_matrix(choice_code);
CREATE INDEX IF NOT EXISTS idx_seat_year ON seat_matrix(year);
