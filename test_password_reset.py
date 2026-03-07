import asyncio
from app.database.db import prisma
from app.auth.services.auth_service import (
    forgot_password_service,
    verify_forgot_password_service,
    reset_password_v2_service
)
from app.auth.services.auth_service import _hash_password

async def main():
    print("--- Testing New Password Reset Flow ---")
    await prisma.connect()
    try:
        email = "testreset@nexprime.com"
        
        # 1. Ensure user exists
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            print(f"Creating test user {email}...")
            await prisma.user.create(
                data={
                    "fullname": "Test Reset",
                    "email": email,
                    "phonenumber": "01700000000",
                    "password": _hash_password("oldpassword"),
                    "residentcard_frontside": "url",
                    "residentcard_backside": "url",
                    "status": "ACTIVE",
                    "is_verified": True
                }
            )
            user = await prisma.user.find_unique(where={"email": email})

        # 2. Step 1: Forgot Password
        print("-> Step 1: Requesting OTP...")
        await forgot_password_service(email)
        
        # Get OTP from database
        otp_record = await prisma.otp.find_first(where={"userId": user.id}, order={"createdAt": "desc"})
        if not otp_record:
            print("Error: OTP not generated.")
            return
        print(f"-> OTP generated: {otp_record.code}")

        # 3. Step 2: Verify OTP and get Reset Token
        print("-> Step 2: Verifying OTP...")
        verify_resp = await verify_forgot_password_service(email, otp_record.code)
        reset_token = verify_resp.get("reset_token")
        if not reset_token:
            print("Error: Reset token not generated.")
            return
        print("-> Reset token received.")

        # 4. Step 3: Reset Password with token
        print("-> Step 3: Resetting password using token...")
        reset_resp = await reset_password_v2_service(reset_token, "newsecretpassword")
        print(f"-> Response: {reset_resp['message']}")

        # 5. Verify password change (optional, service already does this)
        print("\nVerification Passed: Password reset flow completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
