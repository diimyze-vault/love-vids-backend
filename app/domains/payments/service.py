import razorpay
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decimal import Decimal
from loguru import logger
import hmac
import hashlib

from app.core.config import settings
from app.domains.payments.models import TransactionLedger
from app.domains.identity.models import UserProfile

class PaymentService:
    def __init__(self):
        self.client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    async def create_session(self, db: AsyncSession, *, user_id: str, plan_id: str) -> dict:
        plans = {
            # 5 Seconds
            "quick": {"amount": 35},  # 720p
            "pro":   {"amount": 49},  # 1080p
            
            # 10 Seconds
            "magic": {"amount": 55},  # 720p
            "epic":  {"amount": 79},  # 1080p
        }
        plan = plans.get(plan_id)
        if not plan:
            raise Exception("Invalid plan")

        # Create ledger entry (pending)
        ledger = TransactionLedger(
            user_id=user_id,
            amount=Decimal(plan["amount"]),
            type="payment",
            status="pending",
            provider="razorpay"
        )
        db.add(ledger)
        await db.flush()

        # Create Razorpay Order
        order_data = {
            "amount": int(plan["amount"] * 100), # Amount in paise
            "currency": "INR",
            "receipt": f"receipt_{ledger.id}",
            "notes": {
                "user_id": str(user_id),
                "ledger_id": str(ledger.id)
            }
        }
        
        try:
            order = self.client.order.create(data=order_data)
            ledger.provider_transaction_id = order["id"]
            await db.commit()
            
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "key": settings.RAZORPAY_KEY_ID
            }
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            await db.rollback()
            raise Exception("Payment initialization failed")

    async def verify_payment(self, db: AsyncSession, *, user_id: str, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verify the payment signature from the frontend.
        """
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            self.client.utility.verify_payment_signature(params_dict)
            
            # Signature valid, find the ledger
            result = await db.execute(
                select(TransactionLedger).where(TransactionLedger.provider_transaction_id == razorpay_order_id)
            )
            ledger = result.scalar_one_or_none()
            
            if ledger:
                await self.complete_payment(db, ledger.id)
                return True
            return False
        except Exception as e:
            logger.error(f"Razorpay verification failed: {e}")
            return False

    async def handle_razorpay_webhook(self, db: AsyncSession, data: dict, signature: str) -> None:
        """
        Handle Razorpay Webhooks for server-side confirmation.
        """
        # Verification logic for webhook would go here
        event = data.get("event")
        if event == "payment.captured":
            order_id = data["payload"]["payment"]["entity"]["order_id"]
            result = await db.execute(
                select(TransactionLedger).where(TransactionLedger.provider_transaction_id == order_id)
            )
            ledger = result.scalar_one_or_none()
            if ledger:
                await self.complete_payment(db, ledger.id)

    async def complete_payment(self, db: AsyncSession, ledger_id: int) -> None:
        result = await db.execute(select(TransactionLedger).where(TransactionLedger.id == ledger_id))
        ledger = result.scalar_one_or_none()
        
        if not ledger or ledger.status == "completed":
            return

        ledger.status = "completed"
        
        await db.commit()
        logger.info(f"Razorpay Payment completed for ledger {ledger_id} for user {ledger.user_id}")

payment_service = PaymentService()
