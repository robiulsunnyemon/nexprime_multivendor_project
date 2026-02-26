from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_main_category_crud():
    print("Testing Main Category CRUD Endpoints...")
    
    # 1. Login as Admin
    login_data = {
        "username": "admin@nexprime.com",
        "password": "admin123"
    }
    # Swagger OAuth2 login uses form data (username/password)
    response = client.post("/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in as Admin")

    # 2. Create Main Category
    new_cat_name = "Test Main Category"
    response = client.post(
        "/categories/admin/main",
        json={"name": new_cat_name},
        headers=headers
    )
    print(f"POST /categories/admin/main status: {response.status_code}")
    if response.status_code != 201:
        print(f"Create failed: {response.text}")
        return
    
    cat_id = response.json()["id"]
    print(f"✓ Created Main Category: {new_cat_name} (ID: {cat_id})")

    # 3. Update Main Category
    updated_name = "Updated Test Main Category"
    response = client.patch(
        f"/categories/admin/main/{cat_id}",
        json={"name": updated_name},
        headers=headers
    )
    print(f"PATCH /categories/admin/main/{cat_id} status: {response.status_code}")
    if response.status_code != 200:
        print(f"Update failed: {response.text}")
        return
    print(f"✓ Updated Main Category name to: {updated_name}")

    # 4. Verify Update in All Categories
    response = client.get("/categories")
    cats = response.json()
    found = False
    for cat in cats:
        if cat["id"] == cat_id and cat["name"] == updated_name:
            found = True
            break
    if found:
        print("✓ Verified update via GET /categories")
    else:
        print("✗ Failed to verify update via GET /categories")

    # 5. Delete Main Category
    response = client.delete(
        f"/categories/admin/main/{cat_id}",
        headers=headers
    )
    print(f"DELETE /categories/admin/main/{cat_id} status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Deleted Main Category successfully")
    else:
        print(f"Delete failed: {response.text}")

    # 6. Verify Deletion
    response = client.get("/categories")
    cats = response.json()
    found = False
    for cat in cats:
        if cat["id"] == cat_id:
            found = True
            break
    if not found:
        print("✓ Verified deletion via GET /categories")
    else:
        print("✗ Failed to verify deletion - category still exists")

if __name__ == "__main__":
    test_main_category_crud()
