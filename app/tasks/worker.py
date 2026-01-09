from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_routes = {
    "app.tasks.vibes.*": "vibe-queue",
}

celery_app.autodiscover_tasks(["app.tasks.vibes", "app.tasks.viral", "app.tasks.payments"])

# Ensure all models are loaded and mappers configured for the worker process
import app.db.base
from sqlalchemy.orm import configure_mappers
configure_mappers()
