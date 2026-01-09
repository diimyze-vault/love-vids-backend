from typing import Optional
from pydantic import BaseModel, validator
from uuid import UUID
from datetime import datetime

class VideoBase(BaseModel):
    title: Optional[str] = None
    prompt: str
    quality: str = "medium"

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class VideoOut(VideoBase):
    id: UUID
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime

    @validator("video_url", pre=True)
    def sign_b2_url(cls, v):
        if v and "backblazeb2.com" in v:
            try:
                from urllib.parse import urlparse
                from app.core.storage import storage_service
                
                parsed = urlparse(v)
                # Remove leading slash to get the key
                key = parsed.path.lstrip('/')
                
                # Generate presigned URL (valid for 1 hour)
                signed_url = storage_service.generate_presigned_url(key)
                if signed_url:
                    return signed_url
            except Exception:
                pass
        return v

    class Config:
        from_attributes = True

class WebhookData(BaseModel):
    id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
