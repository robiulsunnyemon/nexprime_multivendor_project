import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_patch_store():
    try:
        # 1. Login as vendor
        login_data = {"email": "vendor1@nexprime.com", "password": "password123"}
        resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get current store info
        get_resp = httpx.get(f"{BASE_URL}/vendor/store/me", headers=headers)
        print(f"Current Store Info: {get_resp.status_code} {get_resp.json()}")
        
        # 3. Patch store info
        update_data = {
            "name": "Updated Shop Name",
            "bio": "New Bio for the shop",
            "address": "123 New Vendor Street"
        }
        # Note: PATCH /vendor/store/me is Form-Data
        patch_resp = httpx.patch(f"{BASE_URL}/vendor/store/me", data=update_data, headers=headers)
        print(f"Patch Response: {patch_resp.status_code} {patch_resp.json()}")
        
        if patch_resp.status_code == 200:
            print("Successfully updated store!")
            
            # 4. Verify update
            verify_resp = httpx.get(f"{BASE_URL}/vendor/store/me", headers=headers)
            updated_info = verify_resp.json()
            print(f"Verified Name: {updated_info['name']}")
            print(f"Verified Bio: {updated_info['bio']}")
            print(f"Verified Address: {updated_info['address']}")
        else:
            print("Patch failed.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_patch_store()
