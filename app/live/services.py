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
        # 0. Check if live streaming is enabled globally
        setting = await prisma.systemsetting.find_unique(where={"id": 1})
        if setting and not setting.isLiveStreamingEnabled:
            raise HTTPException(
                status_code=403,
                detail="Live streaming is currently disabled by the administrator."
            )

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

        # Generate Host Token using fluent API (livekit-api >= 1.1.0)
        jwt_token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(participant_identity)
            .with_name(f"Streamer {streamer_id}")
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))
            .to_jwt()
        )

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
    async def get_followed_active_streams(user_id: int, skip: int = 0, limit: int = 20):
        # 1. Get followed store vendor IDs
        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={"followedStores": True}
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        vendor_ids = [store.vendorId for store in user.followedStores]
        
        # 2. Get active streams from these vendors with store details
        streams = await prisma.livestream.find_many(
            where={
                "isActive": True,
                "streamerId": {"in": vendor_ids}
            },
            include={
                "streamer": {
                    "include": {
                        "store": True
                    }
                }
            },
            order={"createdAt": "desc"},
            skip=skip,
            take=limit
        )
        
        formatted_streams = []
        for s in streams:
            store = s.streamer.store
            formatted_streams.append({
                "id": s.id,
                "title": s.title,
                "thumbnail": s.thumbnail,
                "offer": s.offer,
                "endDateTime": s.endDateTime,
                "isActive": s.isActive,
                "viewsCount": s.viewsCount,
                "streamerId": s.streamerId,
                "vendorName": s.streamer.fullname,
                "storeName": store.name if store else "Unknown Store",
                "createdAt": s.createdAt,
                "updatedAt": s.updatedAt,
            })
        
        return {
            "totalActiveStreams": len(formatted_streams),
            "streams": formatted_streams
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

        # Generate Viewer Token using fluent API (livekit-api >= 1.1.0)
        jwt_token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(participant_identity)
            .with_name(f"Viewer {user_id}")
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=False,
                can_subscribe=True,
            ))
            .to_jwt()
        )

        return {"token": jwt_token, "stream": stream}

    @staticmethod
    async def stop_stream(stream_id: int, user_id: int, is_admin: bool = False):
        stream = await prisma.livestream.find_unique(where={"id": stream_id})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
            
        if not is_admin and stream.streamerId != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to stop this stream")

        from datetime import datetime
        updated_stream = await prisma.livestream.update(
            where={"id": stream_id},
            data={
                "isActive": False,
                "endDateTime": datetime.utcnow()
            }
        )

        # Notify vendor if stopped by admin
        if is_admin and stream.streamerId != user_id:
            try:
                from app.chat.services import ChatService
                from app.chat.schemas import MessageCreate
                notification_content = f"Your live stream (ID: {stream_id}) has been ended by an admin."
                await ChatService.save_message(
                    sender_id=user_id,
                    data=MessageCreate(
                        content=notification_content,
                        receiverId=stream.streamerId,
                        type="TEXT"
                    )
                )
            except Exception as e:
                # Log error but don't fail the stream stop operation
                print(f"Error sending notification to vendor: {e}")

        return updated_stream
