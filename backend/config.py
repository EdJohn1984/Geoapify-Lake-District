"""
Central configuration for the hiking trip organizer.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# API Configuration
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "01c9293b314a49979b45d9e0a5570a3f")
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Cache Configuration
CACHE_TTL_HOURS = 24

# Route Generation Configuration
DEFAULT_MAX_TRIES = 5
DEFAULT_GOOD_ENOUGH_THRESHOLD = 0.1
SCENIC_SEARCH_RADIUS_KM = 10

# File paths
REGIONS_DIR = BACKEND_DIR / "regions" / "definitions"
WAYPOINTS_DIR = DATA_DIR / "waypoints"

# Allow overriding cache root to a writable location in production (e.g., Render)
CACHE_ROOT = Path(os.getenv("CACHE_ROOT", str(CACHE_DIR)))
SCENIC_CACHE_DIR = CACHE_ROOT / "scenic_points"
FEASIBLE_PAIRS_CACHE_DIR = CACHE_ROOT / "feasible_pairs"

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
DEBUG = FLASK_ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "http://localhost:3000")
]
