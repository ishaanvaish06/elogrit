# LeetCode Contest Analytics & Rating Predictor (Python)

A high-performance asynchronous Python backend for tracking LeetCode programming contests, participant submissions, real-time rankings, LLM performance, and calculating Elo rating predictions using Fast Fourier Transform (FFT).

---

## ⚡ Key Features

- **LeetCode Contest Aggregation**: Ingests upcoming and past Weekly and Biweekly contests from both US (`leetcode.com`) and CN (`leetcode.cn`) endpoints.
- **FFT Elo Rating Prediction Engine (`EloRatingFft`)**: Computes real-time rating predictions and deltas for tens of thousands of participants in seconds using $O(M \log M)$ frequency-domain discrete convolution via Fast Fourier Transform.
- **Real-Time Analytics & Telemetry**:
  - Live ranking progressions and rating curves across all minutes of a contest.
  - Question solve milestones and real-time completion counts over the 90-minute contest window.
- **LLM Performance Benchmarking**: Tracks AI model performance (avg score, max score, acceptance rate, and attempt counts) on contest problems.
- **Automated Schedulers**: Integrated APScheduler running periodic pre-fetches and automatic prediction routines around contest start/end times.
- **Modern Async REST API**: Built on FastAPI, Pydantic v2, and SQLAlchemy 2.0 Async.

---

## 🛠️ Tech Stack

- **Python**: 3.10+ (tested on Python 3.14)
- **Web Framework**: FastAPI & Uvicorn
- **ORM & DB**: SQLAlchemy 2.0 (Async) + aiosqlite (default) / asyncpg (PostgreSQL)
- **Math & FFT**: NumPy & SciPy
- **HTTP Client**: HTTPX (async client with retry and backoff)
- **Scheduler**: APScheduler
- **Testing**: Pytest & pytest-asyncio

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd LC
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env if using PostgreSQL or changing ports
```

### 3. Run Test Suite
```bash
pytest
```

### 4. Start the API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive OpenAPI documentation will be accessible at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Endpoints

### 🏆 Contests
- `GET /api/v1/leetcode/contests`: List contests (supports `status=upcoming|past|all`, `limit`, `offset`)
- `GET /api/v1/leetcode/contests/{slug}`: Retrieve specific contest details
- `GET /api/v1/leetcode/contests/{slug}/questions`: Problem set for the contest
- `GET /api/v1/leetcode/contests/{slug}/rankings`: Contest leaderboard with Elo rating predictions & deltas
- `GET /api/v1/leetcode/contests/{slug}/question-counts`: Minute-by-minute problem solve milestones
- `POST /api/v1/leetcode/contests/{slug}/sync`: Trigger background metadata sync
- `POST /api/v1/leetcode/contests/{slug}/predict`: Trigger full ranking ingestion & FFT rating calculation

### 👤 Users
- `GET /api/v1/leetcode/users/{data_region}/{user_slug}`: User profile and contest stats (US/CN)
- `GET /api/v1/leetcode/users/{data_region}/{user_slug}/history`: User contest history and rating trends
- `GET /api/v1/leetcode/contests/{slug}/users/{data_region}/{user_slug}/realtime`: Real-time rank & rating progression

### 🤖 LLM Benchmarks
- `GET /api/v1/leetcode/llm`: List all tracked AI models
- `GET /api/v1/leetcode/contests/{slug}/llm`: LLM contest performance and problem statistics

---

## 📁 Directory Structure

```
LC/
├── app/
│   ├── main.py                     # FastAPI app entry point & lifespan
│   ├── config.py                   # Pydantic Settings & environment config
│   ├── database.py                 # Async SQLAlchemy engine & session factory
│   ├── models/                     # SQLAlchemy models (Contest, Question, Ranking, etc.)
│   ├── schemas/                    # Pydantic schemas (DTOs & responses)
│   ├── repositories/               # Database operations (CRUD, bulk sync, rating enrichment)
│   ├── services/
│   │   ├── rating/
│   │   │   └── elo_rating_fft.py   # FFT Elo Rating Engine (matching LeetCode algorithm)
│   │   ├── sourcing/               # Scrapers & API clients for US/CN GraphQL & REST
│   │   ├── contest_service.py      # Contest lifecycle (sync, predict, realtime calculations)
│   │   └── scheduler_service.py    # APScheduler cron & interval jobs
│   └── api/
│       ├── router.py               # Root API router
│       └── routes/                 # Route handlers (contests, users, llm)
├── tests/
│   ├── conftest.py                 # Fixtures with in-memory async SQLite
│   ├── test_elo_rating_fft.py      # FFT prediction accuracy test against real contest dataset
│   └── test_api.py                 # Endpoint integration tests
├── requirements.txt
├── .env.example
└── .gitignore
```
