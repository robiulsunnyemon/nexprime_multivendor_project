import httpx
import json
import os

BASE_URL = "http://127.0.0.1:8001"

def login(email, password):
    print(f"\nLogging in as {email}...")
    resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        print("Login successful.")
        return resp.json()["access_token"]
    print(f"Login failed: {resp.status_code} - {resp.text}")
    return None

def test_admin_settings(admin_token):
    print("\n--- Testing Admin System Settings ---")
    # 1. Get current settings
    resp = httpx.get(f"{BASE_URL}/admin/system-settings", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"Current Settings: {resp.json()}")

    # 2. Toggle Live Streaming to False
    print("Toggling isLiveStreamingEnabled to False...")
    resp = httpx.patch(
        f"{BASE_URL}/admin/system-settings", 
        json={"isLiveStreamingEnabled": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"Update Result: {resp.status_code} - {resp.json()}")

    # 3. Check if disabled
    resp = httpx.get(f"{BASE_URL}/admin/system-settings")
    assert resp.json()["isLiveStreamingEnabled"] == False
    print("Verification: Live streaming disabled successfully.")

    # 4. Toggle back to True
    print("Toggling isLiveStreamingEnabled back to True...")
    httpx.patch(
        f"{BASE_URL}/admin/system-settings", 
        json={"isLiveStreamingEnabled": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print("Toggle back success.")

def test_marketing_deletion():
    print("\n--- Testing Marketing Product Deletion ---")
    # Tokens
    admin_token = login("admin@nexprime.com", "admin123")
    cust1_token = login("customer1@nexprime.com", "password123")
    cust2_token = login("customer2@nexprime.com", "password123")

    if not all([admin_token, cust1_token, cust2_token]):
        print("Check if seed.py was run. Credentials not found.")
        return

    # 1. Customer 1 Creates a product
    print("\nCustomer 1 creating a marketing product...")
    files = {'images': ('test.png', open('dummy_img.png', 'rb'), 'image/png')}
    data = {
        "name": "Test Delete Product",
        "goodsType": "Gadget",
        "location": "Dhaka",
        "description": "To be deleted",
        "price": 100.0,
        "publishingFee": 0.50, # check setting in app
        "shippingResponsibility": "CUSTOMER",
        "shippingCharge": 10.0
    }
    # First make sure customer has enough wallet balance if publishing fee is deducted
    # For testing, we might need to top up wallet if seed script didn't give initial balance
    # But usually seed gives initial state.

    resp = httpx.post(
        f"{BASE_URL}/marketing-products",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {cust1_token}"}
    )
    
    if resp.status_code != 200:
        print(f"Product creation failed: {resp.status_code} - {resp.text}")
        # Maybe wallet balance issue. Let's try to proceed if product was already there or if we can bypass.
        # For simplicity, let's look for any product owned by Cust 1 if create fails.
        my_prods = httpx.get(f"{BASE_URL}/marketing-products/my", headers={"Authorization": f"Bearer {cust1_token}"}).json()
        if not my_prods:
             print("Aborting: No product to delete.")
             return
        prod_id = my_prods[0]["id"]
    else:
        prod_id = resp.json()["id"]
        print(f"Product created with ID: {prod_id}")

    # 2. Customer 2 tries to delete Customer 1's product (Should FAIL)
    print(f"\nCustomer 2 attempting to delete product {prod_id}...")
    resp = httpx.delete(
        f"{BASE_URL}/marketing-products/{prod_id}",
        headers={"Authorization": f"Bearer {cust2_token}"}
    )
    print(f"Result (Should be 403): {resp.status_code} - {resp.json()}")

    # 3. Customer 1 deletes their own product (Should SUCCEED)
    # Actually let's test Admin first then Cust 1 for a new one
    # OR Cust 1 then we create another for Admin.
    
    print(f"\nCustomer 1 deleting their own product {prod_id}...")
    resp = httpx.delete(
        f"{BASE_URL}/marketing-products/{prod_id}",
        headers={"Authorization": f"Bearer {cust1_token}"}
    )
    print(f"Result (Should be 200): {resp.status_code} - {resp.json()}")

    # 4. Create another product for Admin deletion test
    print("\nCreating another product for Admin deletion test...")
    files = {'images': ('test2.png', open('dummy_img.png', 'rb'), 'image/png')}
    resp = httpx.post(
        f"{BASE_URL}/marketing-products",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {cust1_token}"}
    )
    if resp.status_code == 200:
        prod_id_2 = resp.json()["id"]
        print(f"Product 2 created ID: {prod_id_2}")
        
        print(f"\nAdmin deleting product {prod_id_2}...")
        resp = httpx.delete(
            f"{BASE_URL}/marketing-products/{prod_id_2}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Result (Should be 200): {resp.status_code} - {resp.json()}")

if __name__ == "__main__":
    admin_tk = login("admin@nexprime.com", "admin123")
    if admin_tk:
        test_admin_settings(admin_tk)
    test_marketing_deletion()
