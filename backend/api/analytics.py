from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from services.traffic_service import traffic_service

router = APIRouter(prefix="/api/analytics", tags=["Aggregate & Macroscopic Analytics (Level 3)"])


@router.get("/macroscopic")
@router.get("/{video_id}/macroscopic")
async def get_macroscopic_analytics(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve full Level 3 macroscopic analytics: turning, O-D, speeds, queues, density, and LOS."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Macroscopic analytics not found for this video.")
    return data


@router.get("/turning-movements")
@router.get("/{video_id}/turning-movements")
async def get_turning_movements(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Classified intersection turning movements (Straight, Left, Right, U-Turn) and approach volumes."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "turning_movements" not in data:
        raise HTTPException(status_code=404, detail="Turning movement data not found.")
    return data["turning_movements"]


@router.get("/od-matrix")
@router.get("/{video_id}/od-matrix")
async def get_od_matrix(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Origin-Destination (O-D) matrix distribution and route split percentages."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "origin_destination" not in data:
        raise HTTPException(status_code=404, detail="Origin-Destination data not found.")
    return data["origin_destination"]


@router.get("/speed-profiles")
@router.get("/{video_id}/speed-profiles")
async def get_speed_profiles(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Corridor speed profiles: Mean Speed, 85th percentile (P85), 15th percentile (P15), and speeding hotspots."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "speed_profiles" not in data:
        raise HTTPException(status_code=404, detail="Speed profiles data not found.")
    return data["speed_profiles"]


@router.get("/lane-volumes")
@router.get("/{video_id}/lane-volumes")
async def get_lane_volumes(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Lane-by-lane volume breakdown, average lane speed, and vehicle modal split percentages."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "lane_volumes" not in data:
        raise HTTPException(status_code=404, detail="Lane volumes data not found.")
    return data["lane_volumes"]


@router.get("/queues")
@router.get("/{video_id}/queues")
async def get_queue_analytics(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Queue length in meters, queued vehicle count, and average dwell delay behind bottlenecks."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "queue_analytics" not in data:
        raise HTTPException(status_code=404, detail="Queue analytics data not found.")
    return data["queue_analytics"]


@router.get("/flow-density")
@router.get("/{video_id}/flow-density")
async def get_flow_density(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Macroscopic Fundamental Diagram (MFD) metrics: Density k, Occupancy O%, Flow Rate q, and Level of Service (LOS)."""
    data = await traffic_service.get_macroscopic_analytics(video_id)
    if not data or "macroscopic_flow" not in data:
        raise HTTPException(status_code=404, detail="Flow-density data not found.")
    return data["macroscopic_flow"]
