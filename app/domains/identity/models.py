from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, foreign_keys="UserProfile.user_id")
    videos = relationship("Video", back_populates="user")


class UserProfile(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), unique=True)
    
    referral_code = Column(String, unique=True, index=True, nullable=False)
    referred_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    
    storage_limit = Column(Integer, default=5)
    storage_used = Column(Integer, default=0)
    
    subscription_tier = Column(String, default="free") # free, pro, ultra
    
    user = relationship("User", back_populates="profile", foreign_keys=[user_id])
    referrer = relationship("User", foreign_keys=[referred_by_id])
