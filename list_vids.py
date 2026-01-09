import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.domains.identity.models import User, UserProfile
from app.domains.vibes.models import Video
from app.core.config import settings

async def list_videos():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Video).order_by(Video.created_at.desc()))
        videos = result.scalars().all()
        for v in videos:
            print(f"ID: {v.id} | Status: {v.status} | ReqID: {v.replicate_job_id} | Created: {v.created_at}")

if __name__ == "__main__":
    asyncio.run(list_videos())
