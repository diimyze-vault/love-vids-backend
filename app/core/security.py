from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict
import httpx

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.identity import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def verify_supabase_jwt(token: str) -> Optional[TokenPayload]:
    """
    Verify the token by calling Supabase Auth API directly.
    This is more reliable than manual JWT decoding as it handles all algorithms
    and project-specific logic.
    """
    try:
        headers = {
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Construct TokenPayload from Supabase user data
                return TokenPayload(
                    sub=user_data["id"],
                    email=user_data.get("email"),
                    role=user_data.get("role", "authenticated")
                )
            else:
                print(f"Supabase Auth Verification Failed: {response.status_code} {response.text}")
                return None
    except Exception as e:
        print(f"Auth Verification Error: {e}")
        return None

async def get_current_user_id(
    token: str = Depends(reusable_oauth2)
) -> str:
    token_data = await verify_supabase_jwt(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return token_data.sub
