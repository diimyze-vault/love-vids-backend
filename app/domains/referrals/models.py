from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Referral(Base):
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    referee_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    
    is_successful = Column(Boolean, default=False)
    successful_at = Column(DateTime, nullable=True)
    
    reward_granted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", foreign_keys=[referrer_id])
    referee = relationship("User", foreign_keys=[referee_id])
