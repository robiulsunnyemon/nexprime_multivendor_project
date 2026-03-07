import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.database.db import prisma
from app.user.services.wallet_service import WalletService
from app.marketing_product.services import MarketingProductService
from app.marketing_product.schemas import MarketingProductCreate

async def main():
    print("--- Testing Customer Wallet System ---")
    await prisma.connect()
    try:
        # 1. Get a test user (customer1)
        user = await prisma.user.find_first(where={"email": "customer1@nexprime.com"})
        if not user:
            print("Test user customer1@nexprime.com not found. Create it first.")
            return

        # 2. Check initial balance
        balance_resp = await WalletService.get_wallet_balance(user.id)
        print(f"-> Initial Balance: ${balance_resp.balance}")

        # 3. Simulate a successful top-up (via Webhook logic simulation)
        topup_amount = 50.0
        print(f"-> Simulating Top-up: ${topup_amount}...")
        await WalletService.add_funds(user.id, topup_amount, description="Test Top-up")
        
        balance_after_topup = await WalletService.get_wallet_balance(user.id)
        print(f"-> Balance after top-up: ${balance_after_topup.balance}")
        assert balance_after_topup.balance == balance_resp.balance + topup_amount

        # 4. Attempt to create Marketing Product with fee deduction
        # Assume publishingFee is 20.0
        product_data = MarketingProductCreate(
            name="Test Marketing Product",
            goodsType="Electronics",
            location="Dhaka",
            price=100.0,
            description="Testing wallet deduction",
            publishingFee=20.0
        )
        
        print(f"-> Creating Marketing Product (Fee: ${product_data.publishingFee})...")
        # We pass an empty list for images for simplicity
        product = await MarketingProductService.create_marketing_product(
            product_data=product_data,
            creator_id=user.id,
            image_files=[]
        )
        print(f"-> Product created: {product.name} (ID: {product.id})")

        # 5. Verify balance deduction
        final_balance = await WalletService.get_wallet_balance(user.id)
        print(f"-> Final Balance: ${final_balance.balance}")
        assert final_balance.balance == balance_after_topup.balance - product_data.publishingFee

        # 6. Check transactions
        txs = await WalletService.get_transactions(user.id)
        print("\nRecent Transactions:")
        for t in txs[:3]:
            print(f"  - {t.type}: ${t.amount} ({t.description})")

        print("\nWallet Verification Passed!")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
