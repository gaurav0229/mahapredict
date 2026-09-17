# Maharashtra Engineering College Admission Predictor Portal

A production-ready MVP for Maharashtra engineering admission prediction with a Next.js frontend and FastAPI backend.

## Tech stack

- Frontend: Next.js 16 + TypeScript + Tailwind CSS
- Backend: FastAPI + Python
- Data: JSON-based seed dataset for colleges and cutoff history
- Deployment pipeline: GitHub Actions with dev, review, staging, and production environments

## Local development

### Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
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

## Database and storage plan

We are currently using a JSON seed file for local development. For production, we should move to a real relational database and store:

- colleges
- branches
- cutoff_history
- users
- saved_predictions

Database schema files:
- backend/db_schema.sql
- backend/models.py
- backend/database.py

## Environment variables

Create a local `.env` file by copying `backend/.env.example` and setting values for:

- DATABASE_URL
- SECRET_KEY
- ALLOWED_ORIGINS
- REDIS_URL

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
