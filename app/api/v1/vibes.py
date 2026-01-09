from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.schemas.vibes import VideoCreate, VideoOut, WebhookData
from app.schemas.responses import UnifiedResponse
from app.domains.vibes.service import vibe_service

router = APIRouter()

@router.post("/generate", response_model=UnifiedResponse[VideoOut])
async def initiate_vibe_generation(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    vibe_in: VideoCreate
) -> Any:
    """
    Validate credits -> Initiate Celery Task -> Return Job ID.
    """
    video = await vibe_service.initiate_generation(db, user_id=user_id, vibe_in=vibe_in)
    return UnifiedResponse(data=video)

@router.get("/{video_id}", response_model=UnifiedResponse[VideoOut])
async def get_vibe_status(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    video = await vibe_service.get_video(db, video_id=video_id, user_id=user_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return UnifiedResponse(data=video)

@router.post("/webhook", response_model=UnifiedResponse[None])
async def ai_provider_webhook(
    data: WebhookData,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Secure endpoint to receive completion pings from AI providers.
    """
    await vibe_service.process_webhook(db, data=data)
    return UnifiedResponse(data=None)

@router.delete("/{video_id}", response_model=UnifiedResponse[bool])
async def delete_vibe(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    """
    Delete a video record and its associated storage file.
    """
    from loguru import logger
    logger.info(f"API: Received delete request for video {video_id}")
    success = await vibe_service.delete_video(db, video_id=video_id, user_id=user_id)
    
    # Final safety commit
    await db.commit()
    logger.info(f"API: Successfully committed deletion for video {video_id}")
    return UnifiedResponse(data=success)
