from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
KB_DIR = DATA_DIR / "knowledge_base"
PROFILE_DIR = ROOT / "data" / "runtime"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES_FILE = SEED_DIR / "schemes_seed.csv"
PARTNERS_FILE = SEED_DIR / "partners_seed.csv"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(",") if x.strip()]
