import logging
import os
import requests
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

        secret_key = settings.STRIPE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")

        try:
            # 1. Try standard v1 Account creation
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
        except stripe.error.StripeError as e:
            err_msg = str(e)
            logger.warning(f"Stripe v1 Account creation failed ({err_msg}). Attempting Stripe v2 API /v2/core/accounts...")

            # 2. Try Stripe v2 Core Accounts API endpoint
            try:
                resp = requests.post(
                    "https://api.stripe.com/v2/core/accounts",
                    headers={
                        "Authorization": f"Bearer {secret_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "contact_email": user.email,
                        "identity": {
                            "country": country,
                        },
                    },
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    res_data = resp.json()
                    stripe_account_id = res_data.get("id")
                    logger.info(f"Successfully created Stripe v2 Account: {stripe_account_id}")
                else:
                    v2_err = resp.text
                    logger.error(f"Stripe v2 Core Accounts creation failed: {v2_err}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{err_msg} - Action Required: Enable Accounts v1 in Stripe Dashboard: https://dashboard.stripe.com/settings/features/feat_accounts_v1_support"
                    )
            except HTTPException:
                raise
            except Exception as v2_ex:
                logger.error(f"Stripe v2 endpoint exception: {v2_ex}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{err_msg} - Action Required: Enable Accounts v1 in Stripe Dashboard: https://dashboard.stripe.com/settings/features/feat_accounts_v1_support"
                )

        await db.user.update(
            where={"id": user_id},
            data={
                "stripeAccountId": stripe_account_id,
                "stripeAccountStatus": "PENDING",
            },
        )
        return stripe_account_id

    @staticmethod
    async def create_onboarding_link(user_id: int) -> str:
        """Generate a Stripe Express onboarding AccountLink URL for vendor."""
        stripe_account_id = await StripeConnectService.get_or_create_express_account(user_id)

        refresh_url = settings.STRIPE_CONNECT_REFRESH_URL or "https://api.nexprimeapp.com/vendor/stripe/onboarding-link"
        return_url = settings.STRIPE_CONNECT_RETURN_URL or "https://api.nexprimeapp.com/vendor/stripe/success"

        if not (refresh_url.startswith("http://") or refresh_url.startswith("https://")):
            refresh_url = "https://api.nexprimeapp.com/vendor/stripe/onboarding-link"
        if not (return_url.startswith("http://") or return_url.startswith("https://")):
            return_url = "https://api.nexprimeapp.com/vendor/stripe/success"

        try:
            account_link = stripe.AccountLink.create(
                account=stripe_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
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

        # Check if onboarding is completed before creating Express login link
        if not user.isStripeOnboardingCompleted:
            logger.info(f"Vendor {user_id} onboarding incomplete. Returning onboarding link instead of login link.")
            return await StripeConnectService.create_onboarding_link(user_id)

        try:
            login_link = stripe.Account.create_login_link(user.stripeAccountId)
            return login_link.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Create Login Link Error: {e}. Falling back to onboarding link.")
            return await StripeConnectService.create_onboarding_link(user_id)

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
