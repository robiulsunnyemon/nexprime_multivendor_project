import requests
import json

BASE_URL = "http://localhost:8000"

def test_product_flow():
    print("Testing Product Module Implementation...")
    
    # Note: Valid vendor token and existing category IDs are required for real testing.
    # This script provides the structure for verification.
    
    # 1. Fetch All Categories (to get IDs)
    response = requests.get(f"{BASE_URL}/categories")
    if response.status_code == 200:
        cats = response.json()
        print(f"Main Categories found: {[c['name'] for c in cats]}")
    else:
        print("Failed to fetch categories")

    # 2. Get all products
    response = requests.get(f"{BASE_URL}/products")
    print(f"GET /products status: {response.status_code}")
    if response.status_code == 200:
        print(f"Total products found: {len(response.json())}")

if __name__ == "__main__":
    print("Verification script created. Ensure the server is running and you have a valid vendor token for protected endpoints.")
    # test_product_flow()
