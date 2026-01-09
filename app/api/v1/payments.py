from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.schemas.responses import UnifiedResponse
from app.domains.payments.service import payment_service

router = APIRouter()

@router.post("/create-order", response_model=UnifiedResponse[Any])
async def create_razorpay_order(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    """
    Initiate a Razorpay Order.
    """
    order = await payment_service.create_session(db, user_id=user_id, plan_id=plan_id)
    return UnifiedResponse(data=order)

from app.schemas.payments import RazorpayVerifySchema

@router.post("/verify", response_model=UnifiedResponse[Any])
async def verify_razorpay_payment(
    data: RazorpayVerifySchema,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    success = await payment_service.verify_payment(
        db, 
        user_id=user_id, 
        razorpay_order_id=data.order_id, 
        razorpay_payment_id=data.payment_id, 
        razorpay_signature=data.signature
    )
    if not success:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    return UnifiedResponse(data={"status": "verified"})

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    await payment_service.handle_stripe_webhook(db, payload, sig_header)
    return {"status": "success"}

@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    data = await request.json()
    signature = request.headers.get("x-razorpay-signature")
    await payment_service.handle_razorpay_webhook(db, data, signature)
    return {"status": "success"}
