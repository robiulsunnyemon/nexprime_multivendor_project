from fastapi import APIRouter, Depends, status
from app.core.current_user import get_vendor
from app.vendor.stripe_connect_service import StripeConnectService

router = APIRouter(prefix="/vendor/stripe", tags=["Vendor - Stripe Connect"])


@router.post("/onboarding-link", status_code=status.HTTP_200_OK, summary="Generate Stripe Connect Onboarding URL")
async def get_stripe_onboarding_link(current_vendor=Depends(get_vendor)):
    url = await StripeConnectService.create_onboarding_link(current_vendor.id)
    return {"url": url}


@router.get("/status", status_code=status.HTTP_200_OK, summary="Get Vendor's Stripe Connect status")
async def get_stripe_status(current_vendor=Depends(get_vendor)):
    return await StripeConnectService.check_account_status(current_vendor.id)


@router.post("/login-link", status_code=status.HTTP_200_OK, summary="Generate Stripe Express Dashboard Login Link")
async def get_stripe_login_link(current_vendor=Depends(get_vendor)):
    url = await StripeConnectService.create_login_link(current_vendor.id)
    return {"url": url}
