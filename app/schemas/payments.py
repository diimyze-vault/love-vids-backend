from pydantic import BaseModel

class RazorpayVerifySchema(BaseModel):
    order_id: str
    payment_id: str
    signature: str

class RazorpayOrderResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
