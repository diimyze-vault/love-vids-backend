# VibeVids.ai Backend

Production-grade FastAPI backend for AI-powered video gift platform.

## Features

- **DDD Architecture**: Domain-driven design for scalability.
- **Supabase Integration**: Auth & PostgreSQL.
- **Celery + Redis**: Asynchronous video generation.
- **Viral Referral System**: Multi-tier rewards (5/10 successful referrals).
- **Payment Ledger**: Immutable transaction logs for Stripe/Razorpay.
- **Unified Response Format**: Neural JSON standard.

## Tech Stack

- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (Async) + Alembic
- Pydantic V2
- Celery + Redis
- Docker Multi-stage builds

## Setup

1. **Environment Variables**
   Copy `.env.example` to `.env` and fill in the values.

   ```bash
   cp .env.example .env
   ```

2. **Run with Docker**

   ```bash
   docker-compose up --build
   ```

3. **Local Development**
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

- `app/api`: API Routers and versioning.
- `app/domains`: Business logic and models (Identity, Vibes, Referrals, Payments).
- `app/db`: Database connection and base classes.
- `app/schemas`: Pydantic validation schemas.
- `app/tasks`: Celery worker tasks.
- `migrations`: Alembic database migrations.
