from backend.api.traffic import router as traffic_router
from backend.api.analytics import router as analytics_router
from backend.api.spatial import router as spatial_router
from backend.api.reasoning import router as reasoning_router
from backend.api.telemetry import router as telemetry_router

__all__ = [
    "traffic_router",
    "analytics_router",
    "spatial_router",
    "reasoning_router",
    "telemetry_router",
]
