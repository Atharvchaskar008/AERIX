import json
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import cv2
import numpy as np

from backend.core.config import settings
from backend.core.database import mongo_manager

logger = logging.getLogger("aerix.traffic_service")


class TrafficService:
    """Core service bridging FastAPI endpoints with the AERIX ML pipeline and MongoDB."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            "status": "idle",
            "progress": 0,
            "video_id": None,
            "frames_processed": 0,
            "total_frames": 0,
            "message": "System ready.",
            "error": None,
        }
        self._lock = threading.Lock()
        self._latest_frame_jpeg: Optional[bytes] = None
        self._cached_results: Optional[Dict[str, Any]] = None
        
        # Load local results into memory and sync to MongoDB
        self._sync_initial_results()

    def _sync_initial_results(self):
        """Loads level1_results.json and syncs to MongoDB if available."""
        results_file = settings.RESULTS_FILE
        if results_file.exists():
            try:
                with open(results_file, "r", encoding="utf-8") as f:
                    self._cached_results = json.load(f)
                
                # Check if we should insert into MongoDB
                sync_db = mongo_manager.get_sync_db()
                if sync_db is not None and self._cached_results:
                    video_id = self._cached_results.get("video_id", "level1_demo")
                    # Upsert run document
                    sync_db.runs.update_one(
                        {"video_id": video_id},
                        {"$set": {**self._cached_results, "updated_at": datetime.utcnow().isoformat()}},
                        upsert=True
                    )
                    logger.info("Synced %s results document to MongoDB collection 'runs'", video_id)
            except Exception as e:
                logger.warning("Could not sync local results file to MongoDB: %s", e)

    def get_status(self) -> Dict[str, Any]:
        """Returns the current pipeline execution status."""
        with self._lock:
            return dict(self._state)

    def store_live_frame(self, frame_bgr: np.ndarray):
        """Called by the pipeline for every annotated frame to encode JPEG for streaming."""
        try:
            h, w = frame_bgr.shape[:2]
            if w > 1280:
                scale = 1280 / w
                frame_bgr = cv2.resize(frame_bgr, (1280, int(h * scale)))
            _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 72])
            with self._lock:
                self._latest_frame_jpeg = buf.tobytes()
        except Exception:
            pass

    def get_latest_frame_bytes(self) -> Optional[bytes]:
        """Returns JPEG bytes of latest frame."""
        with self._lock:
            return self._latest_frame_jpeg

    def start_processing(
        self,
        video_path: Optional[str] = None,
        sample_rate: int = 3,
        confidence_threshold: float = 0.3,
        model: str = "yolov8s.pt",
        pixels_per_meter: float = 15.0,
        use_real_yolo: bool = True,
        draw_trails: bool = True,
        draw_vectors: bool = True,
    ) -> Dict[str, Any]:
        """Starts asynchronous video processing in a background worker thread."""
        with self._lock:
            if self._state["status"] == "processing":
                return {"status": "busy", "message": "A video processing task is already running."}

        # Resolve video path
        target_video = None
        if video_path and Path(video_path).exists():
            target_video = Path(video_path)
        else:
            # Check recordings or uploads
            for candidate in [
                settings.PROJECT_ROOT.parent / "Recording 2026-08-22 122728.mp4",
                settings.PROJECT_ROOT / "Recording 2026-08-22 122728.mp4",
            ]:
                if candidate.exists():
                    target_video = candidate
                    break

        if not target_video or not target_video.exists():
            raise FileNotFoundError("Video file not found to process. Please upload a video first.")

        video_id = target_video.stem
        output_filename = f"{video_id}_tracked.mp4"
        output_path = settings.VIDEO_DIR / output_filename

        with self._lock:
            self._state = {
                "status": "processing",
                "progress": 0,
                "video_id": video_id,
                "frames_processed": 0,
                "total_frames": 0,
                "message": f"Processing {target_video.name} with YOLO and ByteTrack...",
                "error": None,
            }
            self._latest_frame_jpeg = None

        def _on_progress(data: Dict[str, Any]):
            with self._lock:
                self._state.update(data)

        def _worker():
            try:
                from ml_pipeline.traffic_pipeline import process_traffic_video
                result = process_traffic_video(
                    video_path=str(target_video),
                    output_path=str(output_path),
                    sample_rate=sample_rate,
                    confidence_threshold=confidence_threshold,
                    model=model,
                    use_real_yolo=use_real_yolo,
                    draw_trails=draw_trails,
                    draw_vectors=draw_vectors,
                    pixels_per_meter=pixels_per_meter,
                    progress_callback=_on_progress,
                    frame_callback=self.store_live_frame,
                )

                result["output_video_url"] = f"/videos/{output_filename}"
                result["processed_at"] = datetime.utcnow().isoformat()

                # 1. Update In-Memory Cache
                with self._lock:
                    self._cached_results = result
                    self._state["status"] = "completed"
                    self._state["progress"] = 100
                    self._state["message"] = "Processing completed successfully."

                # 2. Save to local JSON backup
                with open(settings.RESULTS_FILE, "w", encoding="utf-8") as fp:
                    json.dump(result, fp, indent=2, default=str)

                # 3. Persist into MongoDB
                sync_db = mongo_manager.get_sync_db()
                if sync_db is not None:
                    try:
                        # Full run document
                        sync_db.runs.update_one(
                            {"video_id": video_id},
                            {"$set": result},
                            upsert=True
                        )
                        # Granular collections for targeted querying
                        if "macroscopic_analytics" in result:
                            sync_db.analytics.update_one(
                                {"video_id": video_id},
                                {"$set": {"video_id": video_id, **result["macroscopic_analytics"]}},
                                upsert=True
                            )
                        if "spatial_grounding" in result:
                            sync_db.spatial.update_one(
                                {"video_id": video_id},
                                {"$set": {"video_id": video_id, **result["spatial_grounding"]}},
                                upsert=True
                            )
                        if "network_reasoning" in result:
                            sync_db.reasoning.update_one(
                                {"video_id": video_id},
                                {"$set": {"video_id": video_id, **result["network_reasoning"]}},
                                upsert=True
                            )
                        logger.info("Persisted pipeline results for %s into MongoDB collections", video_id)
                    except Exception as me:
                        logger.warning("Error saving to MongoDB: %s", me)

            except Exception as exc:
                logger.error("Pipeline failure: %s", exc, exc_info=True)
                with self._lock:
                    self._state["status"] = "error"
                    self._state["error"] = str(exc)
                    self._state["message"] = f"Pipeline failed: {exc}"

        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()

        return {
            "status": "processing",
            "message": "AERIX traffic processing started in background.",
            "video_id": video_id,
            "target_video": str(target_video),
        }

    async def get_all_runs(self) -> List[Dict[str, Any]]:
        """Fetch list of all runs from MongoDB or local cache."""
        async_db = mongo_manager.get_async_db()
        if async_db is not None:
            try:
                cursor = async_db.runs.find({}, {
                    "video_id": 1,
                    "status": 1,
                    "frames_processed": 1,
                    "unique_tracks": 1,
                    "class_counts": 1,
                    "processed_at": 1,
                    "output_video_url": 1,
                    "_id": 0
                })
                runs = await cursor.to_list(length=100)
                if runs:
                    return runs
            except Exception as e:
                logger.warning("MongoDB query error: %s", e)

        # Fallback to in-memory cached results
        if self._cached_results:
            return [{
                "video_id": self._cached_results.get("video_id", "demo"),
                "status": self._cached_results.get("status", "completed"),
                "frames_processed": self._cached_results.get("frames_processed", 0),
                "unique_tracks": self._cached_results.get("unique_tracks", 0),
                "class_counts": self._cached_results.get("class_counts", {}),
                "processed_at": self._cached_results.get("processed_at", ""),
                "output_video_url": self._cached_results.get("output_video_url", "/videos/level1_output.mp4")
            }]
        return []

    async def get_run_results(self, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns the complete analytics document for a video_id from MongoDB or cache."""
        async_db = mongo_manager.get_async_db()
        if async_db is not None:
            try:
                query = {"video_id": video_id} if video_id else {}
                doc = await async_db.runs.find_one(query, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                logger.warning("MongoDB query error: %s", e)

        # Fallback to local cached document
        if self._cached_results:
            return self._cached_results
        return None

    async def get_macroscopic_analytics(self, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch Level 3 Macroscopic traffic analytics."""
        run = await self.get_run_results(video_id)
        if run:
            return run.get("macroscopic_analytics", {})
        return None

    async def get_spatial_grounding(self, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch Spatial Grounding & GeoJSON maps."""
        run = await self.get_run_results(video_id)
        if run:
            return run.get("spatial_grounding", {})
        return None

    async def get_network_reasoning(self, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch Network Reasoning diagnostics."""
        run = await self.get_run_results(video_id)
        if run:
            return run.get("network_reasoning", {})
        return None

    async def get_telemetry_tracks(self, video_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch vehicle tracking and kinematics summaries."""
        run = await self.get_run_results(video_id)
        if run:
            return run.get("tracks", [])
        return []


# Global service singleton
traffic_service = TrafficService()
