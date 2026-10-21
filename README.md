# InternPilot AI — Core Platform

**InternPilot AI** is an AI-powered co-pilot that helps students discover verified internship opportunities, investigate employer credibility, match opportunities to candidate profiles, prepare recruiter outreach, and track application lifecycles.

> **Current Status**: **Phase 1: Foundation (Complete)**  
> Establishes the production-grade modular monorepo, Next.js frontend, FastAPI backend, SQLAlchemy 2.0 ORM, Alembic migration engine, Redis + Celery worker foundation, Docker containerization, structured logging, and live infrastructure telemetry.

---

## 1. System Architecture

```
Internships bot/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automated CI: lint, types, pytest, frontend check
├── ai-job-search/                 # Vendored Claude Code job-application workflow (MIT)
├── backend/                       # Python FastAPI Backend Service
│   ├── alembic/                   # Database schema migrations
│   │   ├── versions/
│   │   │   └── 0001_initial_baseline.py
│   │   └── env.py
│   ├── app/
│   │   ├── api/v1/                # Versioned REST endpoints
│   │   │   ├── endpoints/health.py # Health & liveness probes
│   │   │   └── api.py
│   │   ├── core/                  # Core configurations & structured logging
│   │   │   ├── config.py          # Pydantic v2 BaseSettings
│   │   │   └── logging.py         # JSON structured log formatting
│   │   ├── db/                    # SQLAlchemy 2.0 async engine & sessions
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── modules/               # Domain-driven feature modules
│   │   │   └── health/            # Health schemas & diagnostic service
│   │   ├── worker/                # Celery background job worker
│   │   │   └── celery_app.py
│   │   └── main.py                # FastAPI lifecycle, CORS, middleware
│   ├── tests/                     # Pytest suite with async mock probes
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                      # Next.js App Router Frontend
│   ├── app/
│   │   ├── status/page.tsx        # Live infrastructure status dashboard
│   │   ├── globals.css            # Tailwind CSS & glassmorphic styling
│   │   ├── layout.tsx             # Root layout with navigation & SEO
│   │   └── page.tsx               # Platform overview & connectivity probe
│   ├── components/                # Modular React UI components
│   │   └── StatusCard.tsx
│   ├── lib/                       # API service layer (real calls, no mocks)
│   │   └── api.ts
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json              # Strict TypeScript configuration
├── .env.example                   # Master environment variables template
├── .gitignore
├── docker-compose.yml             # Local multi-container orchestration
└── README.md
```

---

## 2. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript (Strict Mode), Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, Pydantic v2 (`pydantic-settings`).
- **Database & ORM**: PostgreSQL 16, SQLAlchemy 2.0 (Async Engine via `asyncpg`).
- **Database Migrations**: Alembic.
- **Asynchronous Workers & Caching**: Redis 7, Celery 5.
- **Containerization**: Docker, Docker Compose (with health checks).
- **Testing**: Pytest, `pytest-asyncio`, HTTPX for backend; TypeScript compiler (`tsc --noEmit`) for frontend.

---

## 3. Quick Start (Docker Compose)

The easiest way to boot the complete stack (Postgres, Redis, FastAPI Backend, Celery Worker, and Next.js Frontend) is using Docker Compose:

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Launch All Services
```bash
docker compose up --build
```

### 3. Verify Health
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
- **Live System Status**: [http://localhost:3000/status](http://localhost:3000/status)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **API Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 4. Local Development Setup (Direct)

### Backend Setup (Python 3.12)

1. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Linux / macOS
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the FastAPI Development Server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. (Optional) Start Celery Worker:
   ```bash
   celery -A app.worker.celery_app.celery_app worker --loglevel=info
   ```

### Frontend Setup (Node.js 20+)

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run Next.js Development Server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Running Tests & Quality Verification

### Backend Tests
```bash
cd backend
pytest -v
```

### Backend Type Checking & Linting
```bash
cd backend
mypy app --ignore-missing-imports
flake8 app
```

### Frontend Type Checking
```bash
cd frontend
npm run typecheck
```

---

## 6. Health & Diagnostics API

The `/api/v1/health` endpoint actively tests backing services and reports structured JSON:

```json
{
  "status": "healthy",
  "environment": "development",
  "version": "0.1.0",
  "timestamp": "2026-10-11T15:20:00Z",
  "database": {
    "status": "connected",
    "latency_ms": 1.45,
    "details": "Database responding normally",
    "error": null
  },
  "redis": {
    "status": "connected",
    "latency_ms": 0.82,
    "details": "Redis responded to PING",
    "error": null
  },
  "meta": {
    "app_name": "InternPilot AI API",
    "api_prefix": "/api/v1"
  }
}
```

- When PostgreSQL or Redis is unreachable, the endpoint returns `"status": "degraded"` or `"status": "unhealthy"` (HTTP 503) with the specific error payload, empowering real-time alerting and Kubernetes container health probes.

---

## 7. AI Job Search Workflow (vendored)

[`ai-job-search/`](ai-job-search/) contains a vendored copy of [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) (MIT). It is a Claude Code workflow for profiling yourself, scraping job portals, scoring fit, drafting tailored LaTeX CVs and cover letters with a reviewer agent, interview prep, and outcome tracking. It runs independently of the backend and frontend.

```bash
cd ai-job-search
python tools/install_portal_clis.py   # requires Bun
claude                                # then: /setup, /scrape, /apply <url>, /interview, /outcome
```

Prerequisites: Claude Code, Python 3.10+, [Bun](https://bun.sh), and a LaTeX distribution with `lualatex`/`xelatex`. The bundled portal searches target Danish job boards plus LinkedIn and freehire.me; use `/add-portal` to generate one for another market. See [`ai-job-search/VENDORED.md`](ai-job-search/VENDORED.md) for the upstream commit and update steps.
