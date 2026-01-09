import asyncio
import httpx
from celery import shared_task
from loguru import logger
from sqlalchemy.future import select

from app.tasks.worker import celery_app
from app.db.session import AsyncSessionLocal
from app.domains.identity.models import User, UserProfile
from app.domains.vibes.models import Video
import app.db.base # Ensure all models are registered for SQLAlchemy


from sqlalchemy.orm import configure_mappers
configure_mappers() # Force resolution of all relationships

from app.core.config import settings

@celery_app.task(name="app.tasks.vibes.run_video_generation_task", bind=True)
def run_video_generation_task(self, video_id: str):
    """
    Asynchronous Worker: Integrate with AI APIs (Replicate/Leonardo).
    Handle long-running generations.
    """
    # This is a synchronous wrapper for the async task if needed, 
    # but Celery tasks are usually better off using a separate event loop if they need async.
    return asyncio.run(_run_video_generation(video_id))

async def _run_video_generation(video_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        
        if not video:
            logger.error(f"Video {video_id} not found in database")
            return

        video.status = "processing"
        await db.commit()

        # --- MOCK GENERATION LOGIC (For Testing/No Credits) ---
        USE_MOCK = True
        
        if USE_MOCK:
            logger.info(f"Using MOCK generation for video {video_id}")
            await asyncio.sleep(3) # Simulate processing time
            
            # Reliable public sample video (Google Storage)
            # Note: This mock source is Horizontal (16:9), but the pipeline works.
            # Real AI generations will be Vertical (9:16).
            mock_source_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4"
            
            try:
                # 1. Download the royalty-free video
                async with httpx.AsyncClient() as dl_client:
                    dl_res = await dl_client.get(mock_source_url)
                    if dl_res.status_code != 200:
                        raise Exception("Failed to download mock source video")
                    video_content = dl_res.content
                
                # 2. Upload to B2 Storage
                from app.core.storage import storage_service
                import io
                import uuid
                
                file_name = f"vibe_outputs/{uuid.uuid4()}.mp4"
                file_obj = io.BytesIO(video_content)
                
                # Synchronous upload (acceptable for worker task)
                b2_url = storage_service.upload_file(file_obj, file_name, "video/mp4")
                
                # 3. Update Database
                video.video_url = b2_url
                video.thumbnail_url = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&q=80"
                video.status = "ready"
                
                await db.commit()
                logger.info(f"MOCK SUCCEEDED: Video uploaded to B2 at {b2_url}")
                return

            except Exception as e:
                logger.error(f"MOCK FAILED: {e}")
                video.status = "failed"
                await db.commit()
                return
        # ------------------------------------------------------

        try:
            # fal.ai Kling 2.5 Turbo Integration
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://queue.fal.run/{settings.KLING_MODEL}",
                    headers={
                        "Authorization": f"Key {settings.FAL_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": video.prompt,
                        "duration": "5", # Default duration
                        "aspect_ratio": "9:16", # Default to vertical
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"fal.ai API error: {response.text}")
                    video.status = "failed"
                    await db.commit()
                    return

                res_data = response.json()
                logger.info(f"fal.ai response: {res_data}")
                
                request_id = res_data.get("request_id")
                video.replicate_job_id = request_id
                
                status_url = res_data.get("status_url")
                if not status_url and request_id:
                     status_url = f"https://queue.fal.run/{settings.KLING_MODEL}/requests/{request_id}"
                
                await db.commit()
                
                logger.info(f"Initiated fal.ai Kling 2.5 generation: {video_id}, request_id: {request_id}, status_url: {status_url}")

                # Polling loop (fallback for local development where webhooks don't work)
                status = "in_queue"
                max_retries = 120 # ~10 minutes
                retries = 0
                
                while status not in ["succeeded", "completed", "failed"] and retries < max_retries:
                    await asyncio.sleep(5)
                    retries += 1
                    
                    status_res = await client.get(
                        status_url,
                        headers={"Authorization": f"Key {settings.FAL_KEY}"}
                    )
                    
                    if status_res.status_code == 200:
                        status_data = status_res.json()
                        status = status_data.get("status")
                        logger.info(f"Polling video {video_id} status: {status}")
                        
                        if status.lower() in ["succeeded", "completed", "ok"]:
                            video.status = "ready"
                            
                            # Attempt to get video URL from status response first
                            video_url = status_data.get("video", {}).get("url") or status_data.get("output", {}).get("video", {}).get("url")
                            
                            # If not found, fetch the response_url
                            if not video_url and "response_url" in status_data:
                                response_url = status_data["response_url"]
                                logger.info(f"Fetching final result from: {response_url}")
                                try:
                                    final_res = await client.get(
                                        response_url, 
                                        headers={"Authorization": f"Key {settings.FAL_KEY}"}
                                    )
                                    if final_res.status_code == 200:
                                        final_data = final_res.json()
                                        logger.info(f"Final response data: {final_data}")
                                        video_url = final_data.get("video", {}).get("url") or final_data.get("output", {}).get("video", {}).get("url")
                                except Exception as ex:
                                    logger.error(f"Error fetching response_url: {ex}")

                            # Fallback check
                            if not video_url and "output" in status_data:
                                video_url = status_data["output"].get("video", {}).get("url")
                            
                            video.video_url = video_url
                            
                            # Set a default thumbnail if none provided (backend doesn't generate one yet?)
                            # video.thumbnail_url = ... 
                            
                            await db.commit()
                            logger.info(f"Video {video_id} is READY! URL: {video_url}")
                            break
                        elif status == "failed":
                            video.status = "failed"
                            await db.commit()
                            logger.error(f"Video {video_id} FAILED on fal.ai")
                            break
                
                if retries >= max_retries:
                    logger.warning(f"Polling timed out for video {video_id}")

        except Exception as e:
            logger.exception(f"Failed to process generation for video {video_id}")
            video.status = "failed"
            await db.commit()
