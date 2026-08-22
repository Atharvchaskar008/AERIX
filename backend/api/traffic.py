import os
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse

from backend.core.config import settings
from backend.models.traffic_models import ProcessVideoRequest, ProcessingStatusResponse
from services.traffic_service import traffic_service

router = APIRouter(prefix="/api/traffic", tags=["Traffic & Pipeline"])


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a drone traffic video file."""
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}"
        )

    save_path = settings.UPLOAD_DIR / file.filename
    try:
        with open(save_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return {
            "status": "success",
            "filename": file.filename,
            "video_path": str(save_path),
            "size_bytes": len(content),
            "message": "Video uploaded successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")


@router.post("/process", response_model=Dict[str, Any])
async def process_video(request: Optional[ProcessVideoRequest] = None):
    """Trigger the AERIX autonomous traffic pipeline on a video."""
    req = request or ProcessVideoRequest()
    try:
        result = traffic_service.start_processing(
            video_path=req.video_path,
            sample_rate=req.sample_rate,
            confidence_threshold=req.confidence_threshold,
            model=req.model,
            pixels_per_meter=req.pixels_per_meter,
            use_real_yolo=req.use_real_yolo,
            draw_trails=req.draw_trails,
            draw_vectors=req.draw_vectors,
        )
        return result
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")


@router.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status():
    """Retrieve real-time processing status and progress percentage."""
    return traffic_service.get_status()


@router.get("/frame")
async def get_live_frame():
    """Retrieve the single latest live annotated frame as JPEG."""
    frame_bytes = traffic_service.get_latest_frame_bytes()
    if not frame_bytes:
        # Return transparent 1x1 GIF or 204
        return Response(status_code=204)
    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@router.get("/stream")
async def get_live_mjpeg_stream():
    """Stream live annotated frames as continuous multipart MJPEG."""
    async def frame_generator():
        prev_frame = None
        while True:
            frame_bytes = traffic_service.get_latest_frame_bytes()
            if frame_bytes and frame_bytes != prev_frame:
                prev_frame = frame_bytes
                header = f"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: {len(frame_bytes)}\r\n\r\n".encode("utf-8")
                yield header + frame_bytes + b"\r\n"
            await asyncio.sleep(0.08)  # ~12 FPS stream rate

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/runs", response_model=List[Dict[str, Any]])
async def list_runs():
    """List all processed traffic video runs recorded in MongoDB."""
    return await traffic_service.get_all_runs()


@router.get("/results")
@router.get("/results/{video_id}")
async def get_results(video_id: Optional[str] = None):
    """Get the full analytics document for a video from MongoDB or cache."""
    results = await traffic_service.get_run_results(video_id)
    if not results:
        raise HTTPException(status_code=404, detail="No analytics results found.")
    return results
