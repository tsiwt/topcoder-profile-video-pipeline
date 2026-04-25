import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
JOBS_DIR = BASE_DIR / "jobs"
ASSETS_DIR = BASE_DIR / "assets"

for d in [UPLOAD_DIR, OUTPUT_DIR, JOBS_DIR]:
    d.mkdir(exist_ok=True)

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# HF model (fallback only — primary is local faster-whisper)
HF_WHISPER_MODEL = "openai/whisper-large-v3-turbo"

# Local whisper model size: tiny, base, small, medium, large-v3
# "base" is recommended: ~150MB, good balance of speed vs accuracy
LOCAL_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_DURATION_SEC = 60

# Topcoder brand colors
TC_COLORS = {
    "red":    "#EF3A3A",
    "yellow": "#FFC900",
    "blue":   "#2C95D7",
    "green":  "#50C878",
    "gray":   "#9D9FA0",
    "white":  "#FFFFFF",
    "dark":   "#1A1A2E",
    "primary":"#2C95D7",
}

RATING_COLORS = {
    "red":    "#EF3A3A",
    "yellow": "#FFC900",
    "blue":   "#2C95D7",
    "green":  "#50C878",
    "gray":   "#9D9FA0",
    "white":  "#FFFFFF",
    "unrated":"#9D9FA0",
}

TRACK_LABELS = {
    "development": "Development",
    "design":      "Design",
    "data_science":"Data Science",
    "qa":          "QA",
    "competitive": "Competitive Programming",
}
