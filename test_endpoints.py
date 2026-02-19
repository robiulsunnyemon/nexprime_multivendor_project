import sys
import os
from fastapi.testclient import TestClient
from app.main import app

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

client = TestClient(app)

def run_tests():
    print("Starting endpoint tests...")
    try:
        with TestClient(app) as client:
            # Root endpoint
            response = client.get("/")
            assert response.status_code == 200
            assert response.json()["message"] == "Welcome to NexPrime API"
            print("✓ Root endpoint passed")

            # Signup validation
            response = client.post("/auth/signup", data={})
            assert response.status_code == 422
            print("✓ Signup validation passed (422 for missing fields)")

            # Login invalid user
            response = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "wrongpassword"})
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid email or password."
            print("✓ Login invalid user passed (401)")

        print("\nAll basic endpoint tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")


if __name__ == "__main__":
    run_tests()
