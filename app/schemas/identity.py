from typing import Optional, List
from app.schemas.vibes import VideoOut
from pydantic import BaseModel, EmailStr
from uuid import UUID

class TokenPayload(BaseModel):
    sub: str  # User ID
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    aud: Optional[str] = None
    exp: Optional[int] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    id: UUID

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserProfileBase(BaseModel):
    referral_code: str
    storage_limit: int
    storage_used: int
    subscription_tier: str

class UserProfileUpdate(BaseModel):
    storage_used: Optional[int] = None

class UserOut(UserBase):
    id: UUID
    profile: Optional[UserProfileBase] = None
    videos: List[VideoOut] = []

    class Config:
        from_attributes = True
