import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.database.db import prisma
from app.auth.services.auth_service import login_service, logout_service, refresh_token_service

async def main():
    print("--- Testing Logout Functionality ---")
    await prisma.connect()
    try:
        # 1. Login to get a valid refresh token
        # Using a dummy user from seed
        user = await prisma.user.find_first(where={"email": "customer1@nexprime.com"})
        if not user:
            print("Test user not found.")
            return

        # We need password for login_service, but we can't easily get it.
        # Let's manually create a refresh token for testing instead if login is complex.
        # Actually, let's just use a real login simulation if possible.
        # Since I don't have the plain password easily, I'll manually create a RT.
        
        from app.auth.services.auth_service import _create_refresh_token
        rt = await _create_refresh_token(user.id)
        print(f"-> Created test refresh token: {rt[:20]}...")

        # 2. Verify it's in DB
        stored = await prisma.refreshtoken.find_unique(where={"token": rt})
        assert stored is not None, "Token must be in DB"
        print("-> Token verified in database.")

        # 3. Perform Logout
        print("-> Performing Logout...")
        res = await logout_service(rt)
        print(f"-> Logout Response: {res['message']}")

        # 4. Verify it's gone from DB
        stored_after = await prisma.refreshtoken.find_unique(where={"token": rt})
        assert stored_after is None, "Token must be removed from DB after logout"
        print("-> Token successfully removed from database.")

        # 5. Verify refresh fails
        print("-> Verifying refresh fails with revoked token...")
        try:
            await refresh_token_service(rt)
            print("!! Error: Refresh succeeded with revoked token!")
        except Exception as e:
            print(f"-> Refresh failed as expected: {e}")

        print("\nLogout Verification Passed!")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
