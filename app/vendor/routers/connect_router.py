from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
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


@router.get("/success", response_class=HTMLResponse, summary="Stripe Onboarding Success Callback Page")
async def stripe_onboarding_success():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stripe Onboarding Completed</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 60px 20px; background: #f8fafc; color: #1e293b; }
            .card { background: white; padding: 40px 24px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); max-width: 380px; margin: 0 auto; }
            .icon-circle { width: 64px; height: 64px; background: #dcfce7; color: #16a34a; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 20px auto; }
            h2 { margin: 0 0 10px 0; color: #0f172a; font-size: 20px; font-weight: 700; }
            p { color: #64748b; font-size: 14px; line-height: 1.5; margin: 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon-circle">✓</div>
            <h2>Stripe Account Connected!</h2>
            <p>Your Stripe Express payout account is set up. You can close this window and return to the app.</p>
        </div>
    </body>
    </html>
    """

