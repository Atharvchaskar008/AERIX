import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import mongo_manager
from backend.core.logger import logger
from backend.api import (
    traffic_router,
    analytics_router,
    spatial_router,
    reasoning_router,
    telemetry_router,
)
from services.traffic_service import traffic_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for MongoDB connection and pipeline initialization."""
    print("\n" + "=" * 60)
    print("AERIX — Autonomous Aerial Traffic Intelligence Platform")
    print("=" * 60)
    
    # 1. MongoDB Connection
    mongo_ok = mongo_manager.connect()
    if mongo_ok:
        print(f"[OK] Connected to MongoDB [{settings.mask_url(settings.MONGODB_URL)}/{settings.MONGODB_DB_NAME}]")
    else:
        print("[WARN] MongoDB unavailable; operating in fast local file-cache mode.")

    # 2. Sync / Cache Initialization
    traffic_service._sync_initial_results()
    print("[OK] Pipeline results synchronized and ready.")

    print("\n" + "=" * 60)
    print("[OK] AERIX Backend Online")
    print(f"  * Swagger Docs  : http://localhost:8000/docs")
    print(f"  * Live Dashboard: http://localhost:8000/")
    print(f"  * Health Check  : http://localhost:8000/health")
    print("=" * 60 + "\n")

    yield

    # Cleanup
    mongo_manager.close()
    print("[AERIX] Shutdown complete.")


app = FastAPI(
    title="AERIX — Aerial Traffic Intelligence & Macroscopic Analytics",
    description="""
**AERIX API** delivers end-to-end aerial traffic computer vision and macroscopic network reasoning:
1. **Detection & Tracking**: YOLOv8 + ByteTrack persistent multi-object tracking.
2. **Object-Level Insight**: Fine-grained vehicle sub-types & real-unit kinematics (km/h, m/s²).
3. **Aggregate Insight (Level 3)**: Turning movements, O-D distribution, speed profiles, lane modal split, queues, density, and LOS.
4. **Spatial Grounding**: SRT drone telemetry projection, road topology snapping, GeoJSON desire lines and queue extents.
5. **Network Reasoning**: Space-time congestion origination, signal performance, weaving & conflict hotspots, obstruction census.
""",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories for Video Playback
app.mount("/videos", StaticFiles(directory=str(settings.VIDEO_DIR)), name="videos")
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Register AERIX Routers
app.include_router(traffic_router)
app.include_router(analytics_router)
app.include_router(spatial_router)
app.include_router(reasoning_router)
app.include_router(telemetry_router)


@app.get("/", tags=["Dashboard"])
async def get_dashboard():
    """Serve the interactive AERIX analytics dashboard."""
    dashboard_file = settings.PROJECT_ROOT / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file, media_type="text/html")
    return {"message": "AERIX API is running. Visit /docs for Swagger documentation."}


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint verifying API and MongoDB status."""
    return {
        "status": "healthy",
        "system": "AERIX Aerial Traffic Platform",
        "version": "1.0.0",
        "mongodb_connected": mongo_manager.is_connected,
        "database_name": settings.MONGODB_DB_NAME,
        "pipeline_status": traffic_service.get_status()["status"],
    }
