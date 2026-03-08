import httpx
import json

BASE_URL = "http://127.0.0.1:8007"

def test_update():
    # 1. Login as customer
    login_data = {"email": "customer1@nexprime.com", "password": "password123"}
    try:
        login_resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.text}")
            return
        token = login_resp.json()["access_token"]
    except Exception as e:
        print(f"Login Error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get my marketing products
    try:
        my_products = httpx.get(f"{BASE_URL}/marketing-products/my", headers=headers).json()
        if not my_products:
            print("No marketing products found for this customer.")
            return
        product_id = my_products[0]["id"]
        print(f"Testing with Product ID: {product_id}")
    except Exception as e:
        print(f"Error fetching products: {e}")
        return

    # 3. Update product
    update_data = {
        "name": "Updated Marketing Name",
        "price": 1500.0,
        "description": "This is an updated description."
    }
    
    try:
        # Using data for Form-data in httpx
        resp = httpx.patch(
            f"{BASE_URL}/marketing-products/{product_id}", 
            data=update_data, 
            headers=headers
        )
        print(f"Update Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("Update Success!")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Update Failed: {resp.text}")
    except Exception as e:
        print(f"Update Error: {e}")

if __name__ == "__main__":
    test_update()
