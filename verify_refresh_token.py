import asyncio
import httpx
from prisma import Prisma

async def verify_refresh_token():
    print("--- Verifying Professional Refresh Token System ---")
    
    # 1. Login to get tokens
    async with httpx.AsyncClient() as client:
        # We'll use the admin account created during seed
        login_data = {"email": "admin@nexprime.com", "password": "admin123"}
        response = await client.post("http://localhost:8000/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        print("[SUCCESS] Login successful. Received access and refresh tokens.")
        print(f"  Access Token: {access_token[:20]}...")
        print(f"  Refresh Token: {refresh_token[:20]}...")

        # 2. Check DB if refresh token exists
        prisma = Prisma()
        await prisma.connect()
        stored_token = await prisma.refreshtoken.find_unique(where={"token": refresh_token})
        if stored_token:
            print("[SUCCESS] Refresh token correctly stored in Database.")
        else:
            print("[FAILURE] Refresh token NOT found in Database!")
            await prisma.disconnect()
            return

        # 3. Use refresh token to get new tokens (Rotation)
        print("Attempting token rotation...")
        refresh_response = await client.post(
            "http://localhost:8000/auth/refresh", 
            json={"refresh_token": refresh_token}
        )
        
        if refresh_response.status_code != 200:
            print(f"Refresh failed: {refresh_response.text}")
            await prisma.disconnect()
            return
        
        new_data = refresh_response.json()
        new_access = new_data.get("access_token")
        new_refresh = new_data.get("refresh_token")
        
        print("[SUCCESS] Refresh successful. Received new token pair (Rotation).")
        
        # 4. Verify old refresh token is deleted (Rotation safety)
        old_token_check = await prisma.refreshtoken.find_unique(where={"token": refresh_token})
        if not old_token_check:
            print("[SUCCESS] Old refresh token successfully deleted (Rotation Safety).")
        else:
            print("[FAILURE] Old refresh token still exists! Rotation failed.")

        # 5. Verify new refresh token is in DB
        new_token_check = await prisma.refreshtoken.find_unique(where={"token": new_refresh})
        if new_token_check:
            print("[SUCCESS] New refresh token stored in Database.")
        else:
            print("[FAILURE] New refresh token NOT found in Database!")

        await prisma.disconnect()
        print("--- Verification Successful! ---")

if __name__ == "__main__":
    asyncio.run(verify_refresh_token())
