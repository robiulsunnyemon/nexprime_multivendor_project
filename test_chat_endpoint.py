import asyncio
from app.chat.services import ChatService
from app.database.db import prisma

async def test_active_users():
    await prisma.connect()
    print("Database connected.")
    
    # 1. Fetch any customer to act as the current user
    user = await prisma.user.find_first(where={"role": "CUSTOMER"})
    
    if not user:
        print("No CUSTOMER found in database to test.")
        await prisma.disconnect()
        return

    print(f"Testing for User ID: {user.id} ({user.fullname})")

    # Fetch another user to chat with
    other_user = await prisma.user.find_first(where={"id": {"not": user.id}})

    if other_user:
        print(f"Creating test messages between {user.fullname} and {other_user.fullname}...")
        
        # Other user sends 2 unread messages to the main user
        await prisma.message.create(data={
            "content": "Hello there!",
            "senderId": other_user.id,
            "receiverId": user.id,
            "isRead": False
        })
        await asyncio.sleep(1) # Ensuring slightly different timestamps
        
        await prisma.message.create(data={
            "content": "Are you available?",
            "senderId": other_user.id,
            "receiverId": user.id,
            "isRead": False
        })
        
        await asyncio.sleep(1)
        
        # Main user replies (read message)
        await prisma.message.create(data={
            "content": "Hi! Yes I am here.",
            "senderId": user.id,
            "receiverId": other_user.id,
            "isRead": True
        })

    # 2. Call the updated service method
    try:
        results = await ChatService.get_active_users_for_customer(user.id)
        
        print("\n--- Active Users / Chat History ---")
        if not results:
             print("No active users/chats found.")
             
        for r in results:
            print(f"User: {r.fullname} (ID: {r.id})")
            print(f"  Online: {r.isOnline}")
            print(f"  Unread Count: {r.unreadCount}")
            print(f"  Profile Image: {r.profileImageUrl}")
            if hasattr(r, 'lastMessage') and r.lastMessage:
                print(f"  Last Message: {r.lastMessage} at {r.lastMessageTime}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error occurred during test: {e}")
        
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_active_users())
