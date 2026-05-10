from __future__ import annotations

import logging
from pathlib import Path

from app import config, db

log = logging.getLogger(__name__)


def _build_opts(job_id: int) -> dict:
    outtmpl = str(config.DOWNLOAD_DIR / f"%(title)s [%(id)s].%(ext)s")

    def hook(d: dict) -> None:
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            pct = (done / total * 100.0) if total else 0.0
            db.update_job(job_id, status="downloading", progress=round(pct, 1))
        elif status == "finished":
            db.update_job(job_id, status="processing", progress=100.0)

    return {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
    }


def run_job(job_id: int, url: str) -> None:
    """Synchronous download worker. Called inside FastAPI BackgroundTasks."""
    try:
        import yt_dlp  # imported lazily so tests can mock it
    except Exception as e:  # pragma: no cover
        db.update_job(job_id, status="error", error=f"yt-dlp import failed: {e}")
        return

    db.update_job(job_id, status="downloading")
    try:
        with yt_dlp.YoutubeDL(_build_opts(job_id)) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            # account for merge_output_format swapping the extension
            p = Path(filepath)
            if not p.exists():
                merged = p.with_suffix(".mp4")
                if merged.exists():
                    p = merged
            db.update_job(
                job_id,
                status="done",
                title=info.get("title"),
                filepath=str(p),
                progress=100.0,
            )
    except Exception as e:
        log.exception("download failed for job %s", job_id)
        db.update_job(job_id, status="error", error=str(e))
