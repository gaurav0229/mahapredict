CREATE TABLE IF NOT EXISTS colleges (
    id VARCHAR(120) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(120) NOT NULL,
    district VARCHAR(120) NOT NULL,
    college_type VARCHAR(80) NOT NULL,
    official_website VARCHAR(255),
    total_seats INTEGER DEFAULT 0,
    average_cutoff DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    college_id VARCHAR(120) NOT NULL REFERENCES colleges(id) ON DELETE CASCADE,
    branch_name VARCHAR(150) NOT NULL,
    intake INTEGER,
    placement_signal VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS cutoff_history (
    id SERIAL PRIMARY KEY,
    college_id VARCHAR(120) NOT NULL REFERENCES colleges(id) ON DELETE CASCADE,
    branch_name VARCHAR(150) NOT NULL,
    category VARCHAR(30) NOT NULL,
    year INTEGER NOT NULL,
    cutoff_percent DOUBLE PRECISION NOT NULL,
    closing_rank INTEGER,
    trend_note TEXT
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

CREATE INDEX IF NOT EXISTS idx_colleges_city ON colleges(city);
CREATE INDEX IF NOT EXISTS idx_colleges_district ON colleges(district);
CREATE INDEX IF NOT EXISTS idx_cutoff_college ON cutoff_history(college_id);
CREATE INDEX IF NOT EXISTS idx_cutoff_category ON cutoff_history(category);
