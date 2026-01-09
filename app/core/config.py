from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VibeVids API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Redis (Celery Broker)
    REDIS_URL: str

    # Supabase Auth
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str

    # AI Providers (fal.ai + Kling 2.5 Turbo)
    FAL_KEY: Optional[str] = None
    KLING_MODEL: str = "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"

    # Payment (Razorpay Priority)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Storage (Backblaze B2 S3-Compatible)
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_ENDPOINT: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None
    B2_REGION_NAME: str = "us-west-004"

    # Viral Referral
    REFERRAL_CODE_LENGTH: int = 7

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://love-vids.vercel.app",
        "https://vibevids.xyz",
        "https://www.vibevids.xyz",
        "https://love-vids-production.up.railway.app",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return v

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
