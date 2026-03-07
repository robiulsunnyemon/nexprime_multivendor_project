from app.database.db import prisma
from fastapi import HTTPException
from app.user.schemas.wallet_schemas import WalletResponse, TransactionResponse
from typing import List

class WalletService:
    @staticmethod
    async def get_or_create_wallet(user_id: int):
        wallet = await prisma.wallet.find_unique(where={"userId": user_id})
        if not wallet:
            wallet = await prisma.wallet.create(data={"userId": user_id, "balance": 0.0})
        return wallet

    @staticmethod
    async def get_wallet_balance(user_id: int) -> WalletResponse:
        wallet = await WalletService.get_or_create_wallet(user_id)
        return WalletResponse(balance=wallet.balance, updatedAt=wallet.updatedAt)

    @staticmethod
    async def get_transactions(user_id: int) -> List[TransactionResponse]:
        txs = await prisma.wallettransaction.find_many(
            where={"userId": user_id},
            order={"createdAt": "desc"}
        )
        return [
            TransactionResponse(
                id=t.id,
                amount=t.amount,
                type=t.type,
                description=t.description,
                createdAt=t.createdAt
            ) for t in txs
        ]

    @staticmethod
    async def add_funds(user_id: int, amount: float, description: str = "Wallet Top-up"):
        async with prisma.tx() as tx:
            # 1. Update wallet
            wallet = await WalletService.get_or_create_wallet(user_id)
            await tx.wallet.update(
                where={"userId": user_id},
                data={"balance": {"increment": amount}}
            )
            
            # 2. Record transaction
            await tx.wallettransaction.create(
                data={
                    "userId": user_id,
                    "amount": amount,
                    "type": "TOPUP",
                    "description": description
                }
            )

    @staticmethod
    async def deduct_funds(user_id: int, amount: float, description: str):
        async with prisma.tx() as tx:
            wallet = await WalletService.get_or_create_wallet(user_id)
            if wallet.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient wallet balance.")

            await tx.wallet.update(
                where={"userId": user_id},
                data={"balance": {"decrement": amount}}
            )
            
            await tx.wallettransaction.create(
                data={
                    "userId": user_id,
                    "amount": amount,
                    "type": "FEE_DEDUCTION",
                    "description": description
                }
            )
