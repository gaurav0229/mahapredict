# MahaPredict — Maharashtra Engineering College Admission Predictor Portal

A Maharashtra engineering admission predictor with a Next.js frontend and FastAPI backend, backed by real MHT-CET CAP cutoff and seat-matrix data (2023, 2024, 2026 - all CAP rounds, quota levels and stages) extracted from the official State CET Cell PDFs.

## Tech stack

- Frontend: Next.js 16 + TypeScript + Tailwind CSS
- Backend: FastAPI + Python + SQLAlchemy
- Database: PostgreSQL (Supabase)
- Deployment pipeline: GitHub Actions with dev, review, staging, and production environments

## Local development

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then fill in real values - see Environment variables below
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000

## Production deployment workflow

1. Push to develop branch for dev deployment
2. Open PR to review branch for human approval
3. Merge to main for staging environment
4. Final production deployment after review approval

## Recommended production architecture

- Frontend: Vercel
- Backend: Render or Azure App Service
- Database: PostgreSQL (Supabase / Neon / Azure Database for PostgreSQL)
- Cache: Redis optional for rate limiting and sessions
- Secrets: environment variables only

## Data pipeline

Real cutoff and seat-availability data lives in Postgres, populated from the official CAP PDFs:

- `backend/db_schema.sql` — schema: `colleges`, `branches`, `cutoff_history`, `seat_matrix`, `users`, `saved_predictions`
- `backend/extract_cap_data.py` — extracts cutoff/seat-matrix PDFs (in `backend/supabase_import/official_cap_<year>/`) into normalized CSVs. Checkpointed per-file (`--file`/`--year`) and resumable; see its module docstring for the parsing approach and known PDF-format quirks.
- `backend/import_to_supabase.py` — bulk-loads the extracted CSVs into Postgres via `COPY`, with conflict handling for the AI-quota merit list's multi-candidate rows.
- `backend/models.py` / `backend/database.py` — SQLAlchemy models and connection, read from `DATABASE_URL`.

To add a new year's data: drop the official CAP cutoff/seat-matrix PDFs into `backend/supabase_import/official_cap_<year>/`, run `extract_cap_data.py`, then `import_to_supabase.py`.

## Environment variables

Create a local `backend/.env` by copying `backend/.env.example` and setting real values for:

- `DATABASE_URL` — `postgresql+psycopg://user:password@host:5432/dbname`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `REDIS_URL` (optional)

Never commit real credentials to `.env.example` - it should only ever contain placeholders.

## GitHub pipeline

The CI/CD workflow is defined in `.github/workflows/ci-cd.yml` and follows:

- dev branch -> dev deployment
- review branch / PR review workflow
- main branch -> staging
- production deployment after approval

## Security notes

- CORS restricted to configured origins
- Request throttling middleware active
- Input validation for names and emails
- Payload size checks to prevent abuse
- No secrets committed to source control
- Use managed database credentials and production env secrets only
