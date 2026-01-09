#!/bin/bash
set -e

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Choose command based on PROCESS_TYPE env var
if [ "$PROCESS_TYPE" = "worker" ]; then
    echo "Starting Tame Celery Worker (Pool: Solo)..."
    # --concurrency=1 and --pool=solo reduces memory overhead significantly for 512MB RAM
    exec celery -A app.tasks.worker.celery_app worker --loglevel=info -Q vibe-queue --concurrency=1 --pool=solo
else
    echo "Starting FastAPI API (Lean: Uvicorn Single Process)..."
    # Using uvicorn directly saves memory vs Gunicorn for small containers
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
