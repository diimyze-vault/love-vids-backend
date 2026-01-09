#!/bin/bash
set -e

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Choose command based on PROCESS_TYPE env var
if [ "$PROCESS_TYPE" = "worker" ]; then
    echo "Starting Celery Worker..."
    exec celery -A app.tasks.worker.celery_app worker --loglevel=info -Q vibe-queue
else
    echo "Starting FastAPI API..."
    exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
fi
