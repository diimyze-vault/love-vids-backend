from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from uuid import UUID
import httpx

from app.domains.identity.models import User, UserProfile
from app.domains.referrals.service import referral_service
from app.core.config import settings

class UserService:
    async def get_user_with_profile(self, db: AsyncSession, *, user_id: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.profile),
                joinedload(User.videos)
            )
            .where(User.id == user_id)
        )
        result = result.unique()
        return result.scalar_one_or_none()

    async def sync_user_from_supabase(self, db: AsyncSession, *, user_id: str, referred_by_code: Optional[str] = None) -> User:
        # Check if exists
        user = await self.get_user_with_profile(db, user_id=user_id)
        if user:
            # If user exists but referral was provided later, record it if not already referred
            if referred_by_code and not user.profile.referred_by_id:
                await referral_service.record_signup(db, user_id=user_id, referred_by_code=referred_by_code)
                await db.commit()
                # Reload to get updated profile
                user = await self.get_user_with_profile(db, user_id=user_id)
            return user

        # Retrieve user info from Supabase Admin API
        user_email = f"user_{user_id}@example.com" # Fallback
        
        try:
            headers = {
                "apikey": settings.SUPABASE_SECRET_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    user_data = response.json()
                    user_email = user_data.get("email", user_email)
        except Exception as e:
            print(f"Error fetching user from Supabase Admin API: {e}")

        new_user = User(id=user_id, email=user_email)
        db.add(new_user)
        await db.flush()

        # Create Profile
        referral_code = referral_service.generate_code()
        profile = UserProfile(
            user_id=user_id,
            referral_code=referral_code,
            storage_limit=5
        )
        db.add(profile)
        
        # 3. Record referral attribution if provided
        if referred_by_code:
            await referral_service.record_signup(db, user_id=user_id, referred_by_code=referred_by_code)
        
        await db.commit()
        
        # Return fully loaded user
        return await self.get_user_with_profile(db, user_id=user_id)

user_service = UserService()
