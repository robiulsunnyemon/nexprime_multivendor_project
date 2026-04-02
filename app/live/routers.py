from fastapi import APIRouter, Depends, status
from typing import List
from app.core.current_user import get_current_user
from app.live.schemas import LiveStreamCreate, LiveStreamResponse, LiveTokenResponse, ActiveStreamsListResponse
from app.live.services import LiveStreamService

router = APIRouter(prefix="/live-streams", tags=["Live Streaming"])

@router.post("", response_model=LiveTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_live_stream(
    data: LiveStreamCreate, 
    current_user=Depends(get_current_user)
):
    """
    Create a new live stream and get a broadcaster token.
    """
    return await LiveStreamService.create_live_stream(streamer_id=current_user.id, data=data)

@router.get("/all", response_model=List[LiveStreamResponse])
async def get_all_streams():
    """
    Get all live streams (active and inactive).
    """
    return await LiveStreamService.get_all_streams()

@router.get("/active", response_model=ActiveStreamsListResponse)
async def get_active_streams():
    """
    Get all currently active live streams.
    """
    return await LiveStreamService.get_active_streams()

@router.get("/followed", response_model=List[LiveStreamResponse])
async def get_followed_streams(current_user=Depends(get_current_user)):
    """
    Get active live streams from stores the user follows.
    """
    return await LiveStreamService.get_followed_active_streams(user_id=current_user.id)

@router.post("/{stream_id}/join", response_model=LiveTokenResponse)
async def join_stream(
    stream_id: int, 
    current_user=Depends(get_current_user)
):
    """
    Join a stream to view it. Increases viewsCount and returns a viewer token.
    """
    return await LiveStreamService.join_stream(stream_id=stream_id, user_id=current_user.id)

@router.patch("/{stream_id}/stop", response_model=LiveStreamResponse)
async def stop_stream(
    stream_id: int, 
    current_user=Depends(get_current_user)
):
    """
    Stop an active stream. Can be performed by the streamer or an admin.
    """
    return await LiveStreamService.stop_stream(
        stream_id=stream_id, 
        user_id=current_user.id, 
        is_admin=(current_user.role == "ADMIN")
    )
