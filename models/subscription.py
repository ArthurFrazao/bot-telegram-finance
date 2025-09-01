from pydantic import BaseModel, Field
from uuid import uuid4

class Subscription(BaseModel):
    name: str = Field(..., min_length=1, description="Subscription name")
    description: str = Field(..., description="Subscription description")
    payment_date: int = Field(..., ge=1, le=31, description="Payment date (1-31)")
    uuid: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID")
    card_id: str = Field(..., description="Card ID")
    price: float = Field(..., description="Price")