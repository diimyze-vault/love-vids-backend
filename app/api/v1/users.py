from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.schemas.identity import UserOut, UserProfileUpdate
from app.schemas.responses import UnifiedResponse
from app.domains.identity.service import user_service

router = APIRouter()

@router.get("/me", response_model=UnifiedResponse[UserOut])
async def get_my_profile(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    user = await user_service.get_user_with_profile(db, user_id=user_id)
    if not user:
        # If user doesn't exist in our DB yet but exists in Supabase, create it
        user = await user_service.sync_user_from_supabase(db, user_id=user_id)
    return UnifiedResponse(data=user)

@router.post("/sync", response_model=UnifiedResponse[UserOut])
async def sync_profile(
    referral_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    user = await user_service.sync_user_from_supabase(db, user_id=user_id, referred_by_code=referral_code)
    return UnifiedResponse(data=user)
