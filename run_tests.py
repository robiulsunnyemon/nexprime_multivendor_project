import asyncio
import httpx
from app.main import app
from app.database.db import prisma

async def run_tests():
    # 1. Connect Prisma manually for DB queries within the test script
    # We ignore if it's already connected (FastAPI lifespan will also try to connect)
    if not prisma.is_connected():
        await prisma.connect()
    
    print("Starting tests...")
    
    # 2. Use ASGITransport for newer httpx versions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        
        # --- TEST 1: Login & Followed Streams ---
        resp = await ac.post("/auth/login", json={"email": "customer_test@nexprime.com", "password": "Customer123!"})
        assert resp.status_code == 200, f"Customer login failed: {resp.text}"
        customer_token = resp.json()["access_token"]
        customer_headers = {"Authorization": f"Bearer {customer_token}"}

        resp = await ac.get("/live-streams/followed", headers=customer_headers)
        assert resp.status_code == 200, f"Followed streams fetch failed: {resp.text}"
        streams = resp.json()
        assert len(streams) >= 1, f"Expected at least 1 stream, got {len(streams)}"
        print("✅ Followed streams test passed.")

        # --- TEST 2 & 3: Admin Stop & Notification ---
        resp = await ac.post("/auth/login", json={"email": "admin_test@nexprime.com", "password": "Admin123!"})
        admin_data = resp.json()
        admin_headers = {"Authorization": f"Bearer {admin_data['access_token']}"}
        admin_id = admin_data["user"]["id"]

        stream1 = await prisma.livestream.find_first(where={"title": "Vendor 1 Live Stream"})
        resp = await ac.patch(f"/live-streams/{stream1.id}/stop", headers=admin_headers)
        assert resp.status_code == 200, f"Admin stop stream failed: {resp.text}"
        print("✅ Admin stop stream test passed.")

        vendor1 = await prisma.user.find_unique(where={"email": "vendor1_test@nexprime.com"})
        message = await prisma.message.find_first(
            where={
                "senderId": admin_id,
                "receiverId": vendor1.id,
                "content": {"contains": f"ID: {stream1.id}"}
            }
        )
        assert message is not None, "Notification message not found in DB"
        print("✅ Vendor notification test passed.")

        # --- TEST 4: Sub-category Update ---
        sub_cat = await prisma.subcategory.find_first(where={"name": "Test Sub Category"})
        update_data = {"name": "Updated Test Sub Category"}
        resp = await ac.patch(f"/categories/admin/subcategories/{sub_cat.id}", data=update_data, headers=admin_headers)
        assert resp.status_code == 200, f"Sub-category update failed: {resp.text}"
        assert resp.json()["name"] == "Updated Test Sub Category"
        print("✅ Sub-category update test passed.")

    if prisma.is_connected():
        await prisma.disconnect()
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
