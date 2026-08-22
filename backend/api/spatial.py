from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from services.traffic_service import traffic_service

router = APIRouter(prefix="/api/spatial", tags=["Spatial Grounding & GeoJSON"])


@router.get("/summary")
@router.get("/{video_id}/summary")
async def get_spatial_summary(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve drone flight telemetry summary and spatial projection metrics."""
    data = await traffic_service.get_spatial_grounding(video_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Spatial grounding data not found.")
    return data.get("flight_telemetry") or data.get("telemetry_summary") or data


@router.get("/network-geojson")
@router.get("/{video_id}/network-geojson")
async def get_network_geojson(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Physical road network topology GeoJSON (links, approaches, and individual lane polygons)."""
    data = await traffic_service.get_spatial_grounding(video_id)
    if not data or "road_network_geojson" not in data:
        raise HTTPException(status_code=404, detail="Road network GeoJSON not found.")
    return data["road_network_geojson"]


@router.get("/desire-lines-geojson")
@router.get("/{video_id}/desire-lines-geojson")
async def get_desire_lines_geojson(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Map-native GeoJSON Bézier desire flow lines connecting origin approach to destination approach."""
    data = await traffic_service.get_spatial_grounding(video_id)
    if not data or "desire_lines_geojson" not in data:
        raise HTTPException(status_code=404, detail="Desire lines GeoJSON not found.")
    return data["desire_lines_geojson"]


@router.get("/queue-extents-geojson")
@router.get("/{video_id}/queue-extents-geojson")
async def get_queue_extents_geojson(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Queue extents GeoJSON line segments drawn directly along the physical carriageway."""
    data = await traffic_service.get_spatial_grounding(video_id)
    if not data or "queue_extents_geojson" not in data:
        raise HTTPException(status_code=404, detail="Queue extents GeoJSON not found.")
    return data["queue_extents_geojson"]


@router.get("/per-lane-metrics-geojson")
@router.get("/{video_id}/per-lane-metrics-geojson")
async def get_per_lane_metrics_geojson(video_id: Optional[str] = None) -> Dict[str, Any]:
    """Per-lane traffic metrics bound directly to GeoJSON lane polygons (volume, speed, modal breakdown)."""
    data = await traffic_service.get_spatial_grounding(video_id)
    if not data or "per_lane_metrics_geojson" not in data:
        raise HTTPException(status_code=404, detail="Per-lane metrics GeoJSON not found.")
    return data["per_lane_metrics_geojson"]
