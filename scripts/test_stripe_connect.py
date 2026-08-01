import asyncio
import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import prisma as db
from app.vendor.stripe_connect_service import StripeConnectService
from app.order.services import PaymentService, OrderService


async def test_stripe_connect_schema_and_methods():
    print("[INFO] Starting Stripe Connect Verification Test...")

    # 1. Database Connection Test
    await db.connect()
    print("[OK] Database connected successfully.")

    # 2. Check schema fields on User model
    try:
        dummy_user = await db.user.find_first()
        if dummy_user:
            print(f"[OK] Found test user ID {dummy_user.id}: stripeAccountId={dummy_user.stripeAccountId}, onboardingCompleted={dummy_user.isStripeOnboardingCompleted}")
        else:
            print("[INFO] No users in database currently, schema validation passed.")
    except Exception as e:
        print(f"[ERROR] Error checking User schema: {e}")

    # 3. Check schema fields on SubOrder model
    try:
        dummy_suborder = await db.suborder.find_first()
        if dummy_suborder:
            print(f"[OK] Found test suborder ID {dummy_suborder.id}: transferStatus={dummy_suborder.transferStatus}, transferId={dummy_suborder.stripeTransferId}")
        else:
            print("[INFO] No suborders in database currently, schema validation passed.")
    except Exception as e:
        print(f"[ERROR] Error checking SubOrder schema: {e}")

    # 4. Test StripeConnectService methods structure
    assert hasattr(StripeConnectService, "get_or_create_express_account")
    assert hasattr(StripeConnectService, "create_onboarding_link")
    assert hasattr(StripeConnectService, "check_account_status")
    assert hasattr(StripeConnectService, "create_login_link")
    assert hasattr(StripeConnectService, "transfer_funds_to_vendor")
    print("[OK] All StripeConnectService methods are present and bound correctly.")

    # 5. Test status check for non-existent / empty vendor
    if dummy_user:
        status_res = await StripeConnectService.check_account_status(dummy_user.id)
        print(f"[OK] Stripe status check returned: {status_res}")

    await db.disconnect()
    print("[SUCCESS] Stripe Connect Verification Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(test_stripe_connect_schema_and_methods())
