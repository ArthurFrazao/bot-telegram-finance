from pydantic import BaseModel, Field
from uuid import uuid4

class Card(BaseModel):
    name: str = Field(..., min_length=1, description="Card name")
    payment_date: int = Field(..., ge=1, le=31, description="Payment date (1-31)")
    total_limit: float = Field(..., gt=0, description="Total limit (> 0)")
    uuid: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID")