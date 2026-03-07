import os
from app.database.db import prisma
from fastapi import HTTPException
from livekit import api
from app.live.schemas import LiveStreamCreate
from datetime import timedelta
from app.core.config import settings

class LiveStreamService:
    @staticmethod
    def _get_livekit_creds():
        livekit_url = settings.LIVEKIT_URL
        api_key = settings.LIVEKIT_API_KEY
        api_secret = settings.LIVEKIT_API_SECRET
        return livekit_url, api_key, api_secret

    @staticmethod
    async def create_live_stream(streamer_id: int, data: LiveStreamCreate):
        # 1. Create entry in DB
        stream = await prisma.livestream.create(
            data={
                **data.model_dump(),
                "streamerId": streamer_id,
                "isActive": True
            }
        )

        # 2. Generate Host Token using LiveKit API
        _, api_key, api_secret = LiveStreamService._get_livekit_creds()
        room_name = f"room_{stream.id}"
        participant_identity = f"host_{streamer_id}"

        # Initialize the token instance
        token = api.AccessToken(api_key, api_secret)
        token.identity = participant_identity
        token.name = f"Streamer {streamer_id}"
        
        # Grant permissions for the streamer
        grant = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        token.grants = grant
        
        # Generate token string (12 hours valid)
        jwt_token = token.to_jwt()

        return {"token": jwt_token, "stream": stream}

    @staticmethod
    async def get_all_streams():
        return await prisma.livestream.find_many(
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_active_streams():
        streams = await prisma.livestream.find_many(
            where={"isActive": True},
            order={"createdAt": "desc"}
        )
        total_viewers = sum(s.viewsCount for s in streams)
        
        return {
            "totalActiveStreams": len(streams),
            "totalViewers": total_viewers,
            "streams": streams
        }

    @staticmethod
    async def join_stream(stream_id: int, user_id: int, is_host: bool = False):
        stream = await prisma.livestream.find_unique(where={"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
            
        if not stream.isActive and not is_host:
            raise HTTPException(status_code=400, detail="This stream is no longer active.")

        # Increment views count
        await prisma.livestream.update(
            where={"id": stream_id},
            data={"viewsCount": {"increment": 1}}
        )

        # Generate Viewer Token
        _, api_key, api_secret = LiveStreamService._get_livekit_creds()
        room_name = f"room_{stream.id}"
        participant_identity = f"viewer_{user_id}"

        token = api.AccessToken(api_key, api_secret)
        token.identity = participant_identity
        token.name = f"Viewer {user_id}"

        # Viewers can only subscribe, not publish
        grant = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=False,
            can_subscribe=True,
        )
        token.grants = grant
        
        jwt_token = token.to_jwt()

        return {"token": jwt_token, "stream": stream}

    @staticmethod
    async def stop_stream(stream_id: int, streamer_id: int):
        stream = await prisma.livestream.find_unique(where={"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
            
        if stream.streamerId != streamer_id:
            raise HTTPException(status_code=403, detail="Not authorized to stop this stream")

        from datetime import datetime
        updated_stream = await prisma.livestream.update(
            where={"id": stream_id},
            data={
                "isActive": False,
                "endDateTime": datetime.utcnow()
            }
        )
        return updated_stream
