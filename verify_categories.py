import requests

BASE_URL = "http://localhost:8000"

def test_category_flow():
    print("Testing Category Management Module Flow...")
    
    # 1. Get All Categories
    response = requests.get(f"{BASE_URL}/categories")
    print(f"GET /categories status: {response.status_code}")
    cats = response.json()
    for cat in cats:
        print(f"Main Category: {cat['name']} (ID: {cat['id']}) - Subcats: {len(cat['subCategories'])}")

    # 2. Get Subcategories by Name
    identifier = "Grocery"
    response = requests.get(f"{BASE_URL}/categories/{identifier}/subcategories")
    print(f"GET /categories/{identifier}/subcategories status: {response.status_code}")
    print(f"Subcategories for {identifier}: {response.json()}")

if __name__ == "__main__":
    print("Verification script created. Ensure the server is running (npm run dev or python -m uvicorn app.main:app).")
    # test_category_flow()
