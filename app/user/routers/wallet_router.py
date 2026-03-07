from fastapi import APIRouter, Depends
from app.core.current_user import get_current_user
from app.user.schemas.wallet_schemas import WalletResponse, TopUpRequest, TopUpResponse, TransactionResponse
from app.user.services.wallet_service import WalletService
from app.order.services import PaymentService
from typing import List

router = APIRouter(prefix="/wallet", tags=["Wallet"])

@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(current_user = Depends(get_current_user)):
    """Get current user's wallet balance."""
    return await WalletService.get_wallet_balance(current_user.id)

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_my_transactions(current_user = Depends(get_current_user)):
    """Get wallet transaction history."""
    return await WalletService.get_transactions(current_user.id)

@router.post("/top-up", response_model=TopUpResponse)
async def create_topup_intent(body: TopUpRequest, current_user = Depends(get_current_user)):
    """Create a Stripe Payment Intent for wallet top-up."""
    return await PaymentService.create_wallet_topup_intent(current_user.id, body.amount)
