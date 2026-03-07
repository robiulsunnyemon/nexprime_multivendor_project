from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class WalletResponse(BaseModel):
    balance: float
    updatedAt: datetime

class TopUpRequest(BaseModel):
    amount: float

class TopUpResponse(BaseModel):
    clientSecret: str

class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: str # TOPUP, FEE_DEDUCTION
    description: Optional[str]
    createdAt: datetime
