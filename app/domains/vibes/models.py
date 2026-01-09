from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Video(Base):
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    
    title = Column(String, nullable=True)
    prompt = Column(String, nullable=False)
    
    status = Column(String, default="pending")  # pending, processing, ready, failed
    
    replicate_job_id = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    quality = Column(String, default="medium")  # medium, hq
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("app.domains.identity.models.User", back_populates="videos")
