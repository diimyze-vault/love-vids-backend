from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from loguru import logger

from app.core.config import settings
from app.api.v1 import vibes, users, referrals, payments, storage
from app.schemas.responses import UnifiedResponse, ErrorResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Duration: {process_time:.4f}s"
        )
        return response

app.add_middleware(LoggingMiddleware)

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            status="error",
            message=exc.detail,
            code=str(exc.status_code)
        ))
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(exc)
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(ErrorResponse(
            status="error",
            message="Internal Server Error",
            code="500"
        ))
    )

# Routers
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(vibes.router, prefix=f"{settings.API_V1_STR}/vibes", tags=["vibes"])
app.include_router(referrals.router, prefix=f"{settings.API_V1_STR}/referrals", tags=["referrals"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(storage.router, prefix=f"{settings.API_V1_STR}/storage", tags=["storage"])

@app.get("/", tags=["health"])
async def root():
    return {"status": "success", "message": "VibeVids API is alive"}
