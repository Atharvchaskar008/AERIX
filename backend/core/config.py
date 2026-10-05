import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from multiple possible locations (project root first, then backend)
for env_path in [PROJECT_ROOT / ".env", BACKEND_DIR / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment from: {env_path}")
        break


class Settings:
    def __init__(self):
        # ── MongoDB Settings (Native Python ODM) ──────────────────────────
        self.MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "aerix")
        
        # Legacy/Optional SQL DB (never hard-crash if missing)
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")

        # ── Core Project Paths ───────────────────────────────────────────
        self.PROJECT_ROOT: Path = PROJECT_ROOT
        self.STORAGE_DIR: Path = PROJECT_ROOT / "storage"
        self.UPLOAD_DIR: Path = self.STORAGE_DIR / "uploads"
        self.VIDEO_DIR: Path = self.STORAGE_DIR / "videos"
        self.RESULTS_DIR: Path = self.STORAGE_DIR / "results"
        self.RESULTS_FILE: Path = PROJECT_ROOT / "traffic_analytics_results.json"

        for directory in [self.STORAGE_DIR, self.UPLOAD_DIR, self.VIDEO_DIR, self.RESULTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        # ── Pipeline Defaults ────────────────────────────────────────────
        self.DEFAULT_MODEL: str = os.getenv("AERIX_MODEL", "yolov8s.pt")
        self.DEFAULT_SAMPLE_RATE: int = int(os.getenv("AERIX_SAMPLE_RATE", "3"))
        self.DEFAULT_CONFIDENCE: float = float(os.getenv("AERIX_CONFIDENCE", "0.3"))
        self.DEFAULT_PIXELS_PER_METER: float = float(os.getenv("AERIX_PIXELS_PER_METER", "15.0"))
        
        self.ALLOWED_VIDEO_EXTENSIONS: set[str] = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        self.MAX_VIDEO_SIZE: int = 1000 * 1024 * 1024  # 1 GB
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # ── AI / LLM Diagnostics (Optional) ──────────────────────────────
        self.GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

        print(f"[OK] AERIX Settings Initialized | MongoDB: {self.MONGODB_URL}/{self.MONGODB_DB_NAME}")

    def mask_url(self, url: str) -> str:
        """Mask credentials in URL for safe logging"""
        if "://" not in url or "@" not in url:
            return url
        try:
            scheme, rest = url.split("://", 1)
            credentials, host_part = rest.split("@", 1)
            user = credentials.split(":", 1)[0] if ":" in credentials else credentials
            return f"{scheme}://{user}:****@{host_part}"
        except Exception:
            return url


settings = Settings()
