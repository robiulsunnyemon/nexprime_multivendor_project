import httpx

try:
    resp = httpx.get('http://127.0.0.1:8002/stores')
    stores = resp.json()
    if stores:
        store_id = stores[0]['id']
        print(f"Testing for Store ID: {store_id}")
        count_resp = httpx.get(f"http://127.0.0.1:8002/stores/{store_id}/follower-count")
        print(f"Status Code: {count_resp.status_code}")
        print(f"Response: {count_resp.json()}")
    else:
        print("No stores found in the database.")
except Exception as e:
    print(f"Error: {e}")
