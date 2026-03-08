import httpx

BASE_URL = "http://127.0.0.1:8006"

def create_product():
    # 1. Login as customer
    login_data = {"email": "customer1@nexprime.com", "password": "password123"}
    login_resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create product
    # Valid 1x1 PNG
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    files = [("images", ("test.png", png_content, "image/png"))]
    data = {
        "name": "Test Marketing Product",
        "shippingCharge": 10.0,
        "publishingFee": 0.50,
        "goodsType": "Electronics",
        "location": "Dhaka",
        "description": "Initial description",
        "price": 500.0,
        "shippingResponsibility": "CUSTOMER"
    }
    
    # Ensure wallet has enough funds first (using internal method or just assuming)
    # The create_marketing_product service calls WalletService.deduct_funds
    
    resp = httpx.post(f"{BASE_URL}/marketing-products", data=data, files=files, headers=headers)
    print(f"Create Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    create_product()
