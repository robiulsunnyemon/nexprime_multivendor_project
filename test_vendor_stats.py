import httpx
import json

BASE_URL = "http://127.0.0.1:8008"

def test_stats():
    # 1. Login as vendor
    login_data = {"email": "vendor1@nexprime.com", "password": "password123"}
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

    # 2. Get stats
    try:
        resp = httpx.get(f"{BASE_URL}/vendor/dashboard/stats", headers=headers)
        print(f"Stats Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("Stats Success!")
            data = resp.json()
            # print(json.dumps(data, indent=2))
            for item in data.get("last7DaysEarnings", []):
                print(f"Day: {item.get('day')}, Earnings: {item.get('earnings')}")
        else:
            print(f"Stats Failed: {resp.text}")
    except Exception as e:
        print(f"Stats Error: {e}")

if __name__ == "__main__":
    test_stats()
