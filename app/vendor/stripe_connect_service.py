import logging
import os
import stripe
from datetime import datetime
from fastapi import HTTPException, status
from app.core.config import settings
from app.database.db import prisma as db

logger = logging.getLogger(__name__)

# Initialize Stripe API Key
stripe.api_key = settings.STRIPE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")


class StripeConnectService:

    @staticmethod
    async def get_or_create_express_account(user_id: int, country: str = "JP") -> str:
        """Create or retrieve Stripe Express account for a vendor user."""
        user = await db.user.find_unique(where={"id": user_id})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.stripeAccountId:
            return user.stripeAccountId

        try:
            # Try modern Stripe Connect Account creation using controller configuration
            try:
                account = stripe.Account.create(
                    controller={
                        "stripe_dashboard": {
                            "type": "express",
                        },
                        "fees": {
                            "payer": "application",
                        },
                        "losses": {
                            "payments": "application",
                        },
                    },
                    country=country,
                    email=user.email,
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                    metadata={"user_id": str(user.id)},
                )
            except stripe.error.StripeError as err:
                logger.info(f"Stripe Controller creation attempt: {err}. Falling back to type='express'")
                account = stripe.Account.create(
                    type="express",
                    country=country,
                    email=user.email,
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                    metadata={"user_id": str(user.id)},
                )
            
            stripe_account_id = account.id

            await db.user.update(
                where={"id": user_id},
                data={
                    "stripeAccountId": stripe_account_id,
                    "stripeAccountStatus": "PENDING",
                },
            )
            return stripe_account_id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Account Creation Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{str(e)} - If Accounts v1 is required by your Stripe account, please enable Accounts v1 support at https://dashboard.stripe.com/settings/features/feat_accounts_v1_support"
            )

    @staticmethod
    async def create_onboarding_link(user_id: int) -> str:
        """Generate a Stripe Express onboarding AccountLink URL for vendor."""
        stripe_account_id = await StripeConnectService.get_or_create_express_account(user_id)

        try:
            account_link = stripe.AccountLink.create(
                account=stripe_account_id,
                refresh_url=settings.STRIPE_CONNECT_REFRESH_URL,
                return_url=settings.STRIPE_CONNECT_RETURN_URL,
                type="account_onboarding",
            )
            return account_link.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe AccountLink Error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def check_account_status(user_id: int) -> dict:
        """Check and update vendor's Stripe Account verification status."""
        user = await db.user.find_unique(where={"id": user_id})
        if not user or not user.stripeAccountId:
            return {
                "status": "NOT_CONNECTED",
                "isCompleted": False,
                "stripeAccountId": None,
            }

        try:
            account = stripe.Account.retrieve(user.stripeAccountId)
            is_completed = account.details_submitted
            payouts_enabled = account.payouts_enabled

            account_status = "ACTIVE" if (is_completed and payouts_enabled) else "PENDING"

            await db.user.update(
                where={"id": user_id},
                data={
                    "isStripeOnboardingCompleted": is_completed,
                    "stripeAccountStatus": account_status,
                },
            )

            return {
                "status": account_status,
                "isCompleted": is_completed,
                "payoutsEnabled": payouts_enabled,
                "stripeAccountId": user.stripeAccountId,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Retrieve Account Error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def create_login_link(user_id: int) -> str:
        """Generate a Single Sign-On link to vendor's Stripe Express Dashboard."""
        user = await db.user.find_unique(where={"id": user_id})
        if not user or not user.stripeAccountId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe Account linked to this vendor.",
            )

        try:
            login_link = stripe.Account.create_login_link(user.stripeAccountId)
            return login_link.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Create Login Link Error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def transfer_funds_to_vendor(sub_order_id: int) -> bool:
        """
        Transfer earnings for a SubOrder to the vendor's Stripe Connected Account.
        Called when order/suborder status is updated to DELIVERED.
        """
        sub_order = await db.suborder.find_unique(
            where={"id": sub_order_id},
            include={
                "order": True,
                "store": {
                    "include": {
                        "vendor": True
                    }
                }
            }
        )

        if not sub_order:
            logger.warning(f"SubOrder {sub_order_id} not found for fund transfer.")
            return False

        if sub_order.transferStatus == "TRANSFERRED":
            logger.info(f"SubOrder {sub_order_id} funds already transferred.")
            return True

        if not sub_order.order.isPaid:
            logger.warning(f"Order {sub_order.orderId} is not paid yet. Transfer postponed.")
            return False

        vendor = sub_order.store.vendor
        if not vendor.stripeAccountId or not vendor.isStripeOnboardingCompleted:
            logger.warning(
                f"Vendor {vendor.id} has not completed Stripe onboarding. Funds remain PENDING."
            )
            return False

        earnings = sub_order.vendorEarnings
        if earnings <= 0:
            logger.info(f"SubOrder {sub_order_id} vendor earnings <= 0. Skipping transfer.")
            await db.suborder.update(
                where={"id": sub_order_id},
                data={
                    "transferStatus": "TRANSFERRED",
                    "deliveredAt": datetime.utcnow(),
                }
            )
            return True

        try:
            # Amount conversion for Stripe (integer)
            amount_in_cents = int(earnings)

            transfer = stripe.Transfer.create(
                amount=amount_in_cents,
                currency="jpy",
                destination=vendor.stripeAccountId,
                transfer_group=sub_order.order.transferGroup or f"ORDER_{sub_order.orderId}",
                metadata={
                    "order_id": str(sub_order.orderId),
                    "sub_order_id": str(sub_order.id),
                    "vendor_id": str(vendor.id),
                }
            )

            await db.suborder.update(
                where={"id": sub_order_id},
                data={
                    "stripeTransferId": transfer.id,
                    "transferStatus": "TRANSFERRED",
                    "deliveredAt": datetime.utcnow(),
                }
            )
            logger.info(f"Successfully transferred {earnings} to vendor {vendor.id} for SubOrder {sub_order_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Transfer Error for SubOrder {sub_order_id}: {e}")
            await db.suborder.update(
                where={"id": sub_order_id},
                data={"transferStatus": "FAILED"}
            )
            return False
