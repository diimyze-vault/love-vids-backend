from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.schemas.responses import UnifiedResponse
from app.domains.referrals.service import referral_service

router = APIRouter()

@router.get("/me", response_model=UnifiedResponse[Any])
async def get_my_referral_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    stats = await referral_service.get_stats(db, user_id=user_id)
    return UnifiedResponse(data=stats)

@router.post("/claim", response_model=UnifiedResponse[Any])
async def claim_referral_rewards(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    rewards = await referral_service.claim_rewards(db, user_id=user_id)
    return UnifiedResponse(data=rewards)
