import random
import string
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.domains.referrals.models import Referral
from app.domains.identity.models import UserProfile, User
from app.domains.vibes.models import Video

class ReferralService:
    def generate_code(self, length: int = 7) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    async def get_stats(self, db: AsyncSession, *, user_id: str) -> dict:
        # Count successful referrals (those who created a video)
        res_success = await db.execute(
            select(func.count(Referral.id))
            .where(Referral.referrer_id == user_id, Referral.is_successful == True)
        )
        successful_count = res_success.scalar() or 0
        
        # Count total signed up (pending + successful)
        res_total = await db.execute(
            select(func.count(Referral.id))
            .where(Referral.referrer_id == user_id)
        )
        total_signups = res_total.scalar() or 0
        
        result = await db.execute(
            select(UserProfile.referral_code).where(UserProfile.user_id == user_id)
        )
        code = result.scalar()
        
        return {
            "referral_code": code,
            "successful_referrals": successful_count,
            "total_signups": total_signups,
            "tiers": {
                "tier_1": {"target": 5, "reached": successful_count >= 5},
                "tier_2": {"target": 10, "reached": successful_count >= 10},
            }
        }
    async def record_signup(self, db: AsyncSession, *, user_id: str, referred_by_code: str) -> None:
        if not referred_by_code:
            return

        # Check if already referred to avoid duplicates
        existing = await db.execute(select(Referral).where(Referral.referee_id == user_id))
        if existing.scalar_one_or_none():
            return

        # Find referrer by code
        result = await db.execute(
            select(UserProfile).where(UserProfile.referral_code == referred_by_code)
        )
        referrer_profile = result.scalar_one_or_none()
        
        if not referrer_profile:
            return

        # Create referral record (pending)
        referral = Referral(
            referrer_id=referrer_profile.user_id,
            referee_id=user_id,
            is_successful=False
        )
        db.add(referral)
        
        # Track in profile
        user_profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        user_profile = user_profile_result.scalar_one_or_none()
        if user_profile:
            user_profile.referred_by_id = referrer_profile.user_id

    async def check_and_activate_referral(self, db: AsyncSession, *, referee_id: str) -> None:
        """
        Called when a user creates their first video.
        """
        result = await db.execute(
            select(Referral).where(Referral.referee_id == referee_id, Referral.is_successful == False)
        )
        referral = result.scalar_one_or_none()
        
        if not referral:
            return

        # Check if this is truly the first video
        result = await db.execute(
            select(func.count(Video.id)).where(Video.user_id == referee_id)
        )
        video_count = result.scalar() or 0
        
        if video_count == 1:
            referral.is_successful = True
            referral.successful_at = datetime.utcnow()
            await db.commit()
            
            # Logic for rewarding can be triggered here or via a task
            # self.apply_rewards(db, referral.referrer_id)

    async def claim_rewards(self, db: AsyncSession, *, user_id: str) -> dict:
        # Credits are removed. This could be revamped for other perks later.
        return {"message": "Rewards system is being updated. Stay tuned!"}

referral_service = ReferralService()
