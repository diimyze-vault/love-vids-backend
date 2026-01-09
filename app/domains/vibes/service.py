import httpx
from urllib.parse import urlparse
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from loguru import logger

from app.domains.vibes.models import Video
from app.domains.identity.models import UserProfile
from app.schemas.vibes import VideoCreate, WebhookData
from app.tasks.vibes import run_video_generation_task
from app.domains.referrals.service import referral_service
from app.core.storage import storage_service
from fastapi import HTTPException

class VibeService:
    async def initiate_generation(
        self, db: AsyncSession, *, user_id: str, vibe_in: VideoCreate
    ) -> Video:
        # 0. Fetch profile for quota/metadata
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        # 2. Check storage quota
        if profile.storage_used >= profile.storage_limit:
            raise HTTPException(status_code=429, detail="Storage limit reached")
        # 4. Create Video record
        video = Video(
            user_id=user_id,
            title=vibe_in.title,
            prompt=vibe_in.prompt,
            quality=vibe_in.quality,
            status="pending"
        )
        db.add(video)
        profile.storage_used += 1
        await db.flush()

        # 5. Check if this is the first video for referral activation
        await referral_service.check_and_activate_referral(db, referee_id=user_id)

        # 6. Dispatch Celery Task
        run_video_generation_task.delay(str(video.id))
        
        return video

    async def get_video(self, db: AsyncSession, video_id: UUID, user_id: str) -> Optional[Video]:
        result = await db.execute(
            select(Video).where(Video.id == video_id, Video.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def process_webhook(self, db: AsyncSession, data: WebhookData) -> None:
        # data.id would be replicate_job_id
        result = await db.execute(
            select(Video).where(Video.replicate_job_id == data.id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            return

        if data.status == "succeeded":
            video.status = "ready"
            video.video_url = data.output
            # In a real app, you might also trigger thumbnail generation here
        elif data.status == "failed":
            video.status = "failed"
            # In a real app, you might refund credits here
        
        await db.commit()

    async def delete_video(self, db: AsyncSession, video_id: UUID, user_id: str) -> bool:
        video = await self.get_video(db, video_id=video_id, user_id=user_id)
        if not video:
            logger.warning(f"Delete attempted for non-existent video: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        logger.info(f"Deleting video {video_id} for user {user_id}")

        # 1. Delete from B2 if applicable
        for url_attr in ["video_url", "thumbnail_url"]:
            url = getattr(video, url_attr)
            if url and "backblazeb2.com" in url:
                try:
                    parsed = urlparse(url)
                    # The key is the path after the bucket name, but in B2 S3 API,
                    # the bucket is often part of the hostname or first path part.
                    # Our storage service handles the bucket name via settings.
                    # We just need the actual object key.
                    key = parsed.path.lstrip('/')
                    # If the URL is bucket.endpoint/key, we might need to strip bucket if it's there
                    # But usually lstrip('/') is enough for the key if we use the right endpoint.
                    storage_service.delete_file(key)
                    logger.info(f"Deleted {url_attr} from B2: {key}")
                except Exception as e:
                    logger.error(f"Error deleting {url_attr} from B2: {e}")

        # 2. Update storage count first (while video object is still in session)
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile and profile.storage_used > 0:
            profile.storage_used -= 1
            logger.info(f"Updated storage_used for user {user_id}: {profile.storage_used}")

        # 3. Delete from DB using raw SQL to ensure persistence bypasses any ORM session weirdness
        await db.execute(delete(Video).where(Video.id == video_id))
        
        # Force immediate commit within the service
        await db.commit()
        
        # Expire the user in the session so that the next fetch for 'profile' 
        # (which includes videos) is forced to reload from the DB.
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile:
             db.expire(profile)

        logger.info(f"Video {video_id} permanently deleted and committed.")
        return True

vibe_service = VibeService()
