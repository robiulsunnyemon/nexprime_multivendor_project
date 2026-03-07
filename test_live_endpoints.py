import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load env before importing settings since settings uses Pydantic which loads on import
load_dotenv()

from app.database.db import prisma
from app.live.services import LiveStreamService
from app.live.schemas import LiveStreamCreate
from app.core.config import settings

async def main():
    print("--- Testing Live Streaming Service ---")
    
    await prisma.connect()
    try:
        # Check LiveKit Config
        print(f"LiveKit URL Configuration: {settings.LIVEKIT_URL}")

        # Get a couple dummy users to test with
        users = await prisma.user.find_many(take=2)
        if len(users) < 2:
            print("Not enough users to test.")
            return

        streamer = users[0]
        viewer = users[1]

        print(f"\n1. Testing Create Stream (Streamer ID: {streamer.id})")
        stream_data = LiveStreamCreate(
            thumbnail="https://picsum.photos/400",
            title="Test Live Stream",
            offer="20% OFF",
        )
        created_res = await LiveStreamService.create_live_stream(streamer.id, stream_data)
        stream_id = created_res["stream"].id
        host_token = created_res["token"]
        print(f"-> Stream Created! ID: {stream_id}")
        print(f"-> Host Token (length): {len(host_token)}")

        print("\n2. Testing Get All Streams")
        all_streams = await LiveStreamService.get_all_streams()
        print(f"-> Total Streams: {len(all_streams)}")

        print("\n3. Testing Get Active Streams")
        active_res = await LiveStreamService.get_active_streams()
        print(f"-> Total Active Streams (from summary): {active_res['totalActiveStreams']}")
        print(f"-> Total Viewers (from summary): {active_res['totalViewers']}")
        assert active_res['totalActiveStreams'] >= 1
        assert any(s.id == stream_id for s in active_res['streams']), "Created stream should be in the active list"

        print(f"\n4. Testing Join Stream (Viewer ID: {viewer.id})")
        join_res = await LiveStreamService.join_stream(stream_id, viewer.id)
        viewer_token = join_res["token"]
        print(f"-> Joined successfully! Views Count is now: {join_res['stream'].viewsCount}")
        print(f"-> Viewer Token (length): {len(viewer_token)}")

        print("\n5. Testing Stop Stream")
        stopped_stream = await LiveStreamService.stop_stream(stream_id, streamer.id)
        print(f"-> Stream Stopped. isActive: {stopped_stream.isActive}")
        print(f"-> End Time Logged: {stopped_stream.endDateTime}")

        print("\n6. Verifying that it is no longer active")
        active_after_stop = await LiveStreamService.get_active_streams()
        assert not any(s.id == stream_id for s in active_after_stop['streams']), "Stream should no longer be active"
        print("-> Verification Passed!")

        print("\nAll Tests Executed Successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
