import asyncio
from app.database.db import prisma
from app.user.services.user_service import UserService

async def test_profile_update():
    await prisma.connect()
    
    try:
        # 1. Grab an arbitrary customer
        customer = await prisma.user.find_first(where={"role": "CUSTOMER"})
        if not customer:
            print("No customers found in database.")
            return
            
        print(f"Testing for Customer ID: {customer.id}")
        print(f"Original Full Name: {customer.fullname}")
        print(f"Original Phone Number: {customer.phonenumber}")
        print(f"Original Profile Image: {customer.profileImageUrl}")
        
        # 2. Simulate partial update data
        update_data = {
            "fullname": "Updated Super Name",
            # "phonenumber": None, # Should be ignored and preserve old value
            "profileImageUrl": "https://example.com/new_avatar.png"
            # Omit password & coverImage to test selective updates
        }

        print(f"\nSending Update Data: {update_data}")
        
        # 3. Call the newly created service directly
        updated_customer = await UserService.update_user_profile(user_id=customer.id, update_data=update_data)
        
        # 4. Assert updates
        print(f"\n--- Update Result ---")
        print(f"New Full Name: {updated_customer.fullname}")
        print(f"New Phone Number: {updated_customer.phonenumber}")
        print(f"New Profile Image: {updated_customer.profileImageUrl}")

        if updated_customer.fullname == update_data["fullname"]:
            print("✅ Fullname successfully updated.")
        else:
            print("❌ Fullname update failed.")
            
        if updated_customer.phonenumber == customer.phonenumber:
            print("✅ Phonenumber successfully retained (not overwritten with null).")
        else:
            print("❌ Phonenumber was improperly modified!")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_profile_update())
