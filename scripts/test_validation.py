import os
import sys
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock prisma client
mock_prisma = MagicMock()
mock_prisma.connect = AsyncMock()
mock_prisma.disconnect = AsyncMock()

class MockStore:
    def __init__(self):
        self.id = 10
        self.vendorId = 1

mock_prisma.store.find_unique = AsyncMock(return_value=MockStore())

# Override prisma in app.database.db BEFORE importing app modules
import app.database.db
app.database.db.prisma = mock_prisma

# Now import the app and router modules
from app.main import app
from app.core.current_user import get_vendor
from app.product.services import ProductService
from app.product.schemas import ProductSize
from fastapi.testclient import TestClient

# Mock vendor user
class MockVendor:
    def __init__(self):
        self.id = 1
        self.role = "VENDOR"
        self.status = "ACTIVE"

async def override_get_vendor():
    return MockVendor()

app.dependency_overrides[get_vendor] = override_get_vendor

# Mock ProductService responses
mock_product_response = {
    "id": 1,
    "name": "Test Product",
    "description": "Test description",
    "basePrice": 100.0,
    "stockUnits": 10,
    "size": ["S", "M"],
    "colors": ["RED"],
    "isDiscountSale": False,
    "salePrice": None,
    "discountPercentage": None,
    "shippingResponsibility": "CUSTOMER",
    "shippingCharge": 10.0,
    "total_payable_amount": 100.0,
    "images": ["http://example.com/image.jpg"],
    "storeId": 10,
    "store": {
        "id": 10,
        "name": "Test Store",
        "address": "Test address",
        "photo": "http://example.com/photo.jpg",
        "coverImgUrl": None
    },
    "categories": [],
    "createdAt": datetime.now().isoformat(),
    "updatedAt": datetime.now().isoformat()
}

ProductService.create_product = AsyncMock(return_value=mock_product_response)
ProductService.update_product = AsyncMock(return_value=mock_product_response)

def test_endpoints():
    client = TestClient(app)
    
    print("\n--- 1. Testing POST /vendor/products with VALID size ---")
    data_valid = {
        "name": "Super Shirt",
        "description": "Premium Quality Shirt",
        "basePrice": 1200.0,
        "stockUnits": 50,
        "size": "M,L,XL", # Comma-separated
        "colors": "RED,BLUE",
        "isDiscountSale": "false",
        "shippingCharge": 60.0,
        "category_ids": "[1, 2]"
    }
    # Mocking UploadFile for images
    files = [("images", ("test_image.jpg", b"dummy_content", "image/jpeg"))]
    
    response = client.post("/vendor/products", data=data_valid, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    print("\n--- 2. Testing POST /vendor/products with INVALID size (should return 400) ---")
    data_invalid = data_valid.copy()
    data_invalid["size"] = "M,INVALID_SIZE,XL"
    
    response = client.post("/vendor/products", data=data_invalid, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Invalid size" in response.json()["detail"], "Expected 'Invalid size' error message"

    print("\n--- 3. Testing PATCH /vendor/products/1 with VALID size ---")
    patch_data_valid = {
        "size": "S,XL"
    }
    response = client.patch("/vendor/products/1", data=patch_data_valid)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    print("\n--- 4. Testing PATCH /vendor/products/1 with INVALID size (should return 400) ---")
    patch_data_invalid = {
        "size": "XXL,INVALID_SIZE_2"
    }
    response = client.patch("/vendor/products/1", data=patch_data_invalid)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Invalid size" in response.json()["detail"], "Expected 'Invalid size' error message"

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_endpoints()
