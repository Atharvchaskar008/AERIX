from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from services.traffic_service import traffic_service

router = APIRouter(prefix="/api/reasoning", tags=["Network Reasoning & Diagnostics"])


@router.get("/summary")
@router.get("/{video_id}/summary")
async def get_network_reasoning_summary(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Complete Network Reasoning report including space-time congestion tracing and AI natural language diagnosis."""
    data = await traffic_service.get_network_reasoning(video_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Network reasoning data not found.")
    return data


@router.get("/congestion-origin")
@router.get("/{video_id}/congestion-origin")
async def get_congestion_origin(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Congestion origination diagnosis: Tracing traffic jams back through space and time to the exact start bottleneck."""
    data = await traffic_service.get_network_reasoning(video_id)
    if not data or "congestion_origination" not in data:
        raise HTTPException(status_code=404, detail="Congestion origination data not found.")
    return data["congestion_origination"]


@router.get("/signal-performance")
@router.get("/{video_id}/signal-performance")
async def get_signal_performance(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Traffic signal metrics: starting & discharge headways, saturation flow rate, green utilisation, and cycle failure rate."""
    data = await traffic_service.get_network_reasoning(video_id)
    if not data or "signal_performance" not in data:
        raise HTTPException(status_code=404, detail="Signal performance data not found.")
    return data["signal_performance"]


@router.get("/conflicts")
@router.get("/{video_id}/conflicts")
async def get_weaving_and_conflicts(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Weaving, merging and gap acceptance: lane changes per kilometre, merge behavior, and conflict concentration hotspots."""
    data = await traffic_service.get_network_reasoning(video_id)
    if not data or "weaving_and_conflicts" not in data:
        raise HTTPException(status_code=404, detail="Conflict and weaving data not found.")
    return data["weaving_and_conflicts"]


@router.get("/desire-lines")
@router.get("/{video_id}/desire-lines")
async def get_desire_lines_analysis(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Desire-line analysis: Where road users actually move vs assumed geometry (corner-cutting, lane straddling, informal paths)."""
    data = await traffic_service.get_network_reasoning(video_id)
    desire_data = data.get("desire_line_analysis") or data.get("desire_lines_and_geometry") if data else None
    if not desire_data:
        raise HTTPException(status_code=404, detail="Desire-line deviation data not found.")
    return desire_data


@router.get("/obstructions")
@router.get("/{video_id}/obstructions")
async def get_obstruction_census(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Obstruction census: Double parking, bus-stop blocking, bike-lane obstruction, loading-zone abuse with exact dwell durations."""
    data = await traffic_service.get_network_reasoning(video_id)
    if not data or "obstruction_census" not in data:
        raise HTTPException(status_code=404, detail="Obstruction census data not found.")
    return data["obstruction_census"]
