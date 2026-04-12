import httpx
import asyncio
import os

BASE_URL = "https://api.nexprime.nexcorporate.com" # Assuming this from the screenshot
# If running locally, it might be http://localhost:8000
# Let's try to detect the local port if possible, or just use the one in the environment.
# Looking at the screenshot, it's a production URL but maybe I should test against local.
LOCAL_URL = "http://localhost:8000"

async def test_upload():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        login_res = await client.post(f"{LOCAL_URL}/auth/login", json={
            "email": "vendor1@nexprime.com",
            "password": "password123"
        })
        
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        
        token = login_res.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully.")

        # 2. Create product with images
        print("Creating product...")
        
        # Create a valid 1x1 PNG image file
        png_pixel = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc\x60\x60"
            b"\x60\x00\x00\x00\x04\x00\x01\x12\xaf \x96\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with open("test_image.png", "wb") as f:
            f.write(png_pixel)
            
        files = [
            ("images", ("test_image.png", open("test_image.png", "rb"), "image/png"))
        ]
        
        data = {
            "name": "Test Product Fix",
            "description": "Testing the image upload fix",
            "basePrice": "100",
            "stockUnits": "10",
            "isDiscountSale": "false",
            "shippingCharge": "5",
            "category_ids": "[1, 2]"
        }
        
        try:
            res = await client.post(f"{LOCAL_URL}/vendor/products", data=data, files=files, headers=headers)
        finally:
            # Manually close files if httpx didn't
            for _, f_spec in files:
                f_spec[1].close()
        
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        
        if res.status_code == 201:
            print("SUCCESS: Product created with images!")
        else:
            print("FAILED: Image upload still failing.")
            
        # Cleanup
        os.remove("test_image.png")

if __name__ == "__main__":
    asyncio.run(test_upload())
