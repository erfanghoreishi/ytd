import os
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


AUTH_ENABLED = _bool("YTD_AUTH_ENABLED", False)
USERNAME = os.getenv("YTD_USER", "admin")
PASSWORD_HASH = os.getenv("YTD_PASS_HASH", "")

DOWNLOAD_DIR = Path(os.getenv("YTD_DOWNLOAD_DIR", "downloads")).resolve()
DATA_DIR = Path(os.getenv("YTD_DATA_DIR", "data")).resolve()
DB_PATH = DATA_DIR / "ytd.sqlite3"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
