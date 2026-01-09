from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class TransactionLedger(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String, default="INR")
    
    # payment, credit_purchase, referral_reward, usage
    type = Column(String, nullable=False)
    
    provider = Column(String, nullable=True)  # stripe, razorpay, system
    provider_transaction_id = Column(String, nullable=True, index=True)
    
    status = Column(String, default="pending")  # pending, completed, failed, refunded
    
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
