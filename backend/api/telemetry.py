from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from services.traffic_service import traffic_service

router = APIRouter(prefix="/api/telemetry", tags=["Object Telemetry & Kinematics"])


@router.get("/tracks")
@router.get("/{video_id}/tracks")
async def get_all_tracks(video_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve full list of tracked road users with fine-grained classifications and kinematics."""
    tracks = await traffic_service.get_telemetry_tracks(video_id)
    return tracks


@router.get("/track/{track_id}")
@router.get("/{video_id}/track/{track_id}")
async def get_single_track(track_id: int, video_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve fine-grained details, trajectory history, and instantaneous kinematics for a specific track ID."""
    tracks = await traffic_service.get_telemetry_tracks(video_id)
    for t in tracks:
        if t.get("track_id") == track_id:
            return t
    raise HTTPException(status_code=404, detail=f"Track #{track_id} not found.")


@router.get("/summary")
@router.get("/{video_id}/summary")
async def get_kinematics_summary(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Fleet-wide kinematics summary: Average speed, Max speed, Speed distributions, and Modal counts."""
    run = await traffic_service.get_run_results(video_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run results not found.")
    return {
        "video_id": run.get("video_id"),
        "unique_tracks": run.get("unique_tracks", 0),
        "kinematics_summary": run.get("kinematics_summary", {}),
        "class_counts": run.get("class_counts", {}),
        "fine_grained_class_counts": run.get("fine_grained_class_counts", {}),
    }
