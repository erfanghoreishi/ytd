from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config, db, downloader
from app.auth import require_user

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init()
    yield


app = FastAPI(title="YTD", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

db.init()


@app.get("/", response_class=HTMLResponse)
def index(request: Request, _user: str = Depends(require_user)):
    return templates.TemplateResponse(
        request, "index.html", {"jobs": db.list_jobs()}
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs_fragment(request: Request, _user: str = Depends(require_user)):
    return templates.TemplateResponse(
        request, "_jobs.html", {"jobs": db.list_jobs()}
    )


@app.post("/jobs", response_class=HTMLResponse)
def create_job(
    request: Request,
    background: BackgroundTasks,
    url: str = Form(...),
    _user: str = Depends(require_user),
):
    url = url.strip()
    if not url:
        raise HTTPException(400, "URL is required")
    job_id = db.create_job(url)
    background.add_task(downloader.run_job, job_id, url)
    return templates.TemplateResponse(
        request, "_jobs.html", {"jobs": db.list_jobs()}
    )


@app.get("/jobs/{job_id}/file")
def download_file(job_id: int, _user: str = Depends(require_user)):
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if job["status"] != "done" or not job["filepath"]:
        raise HTTPException(409, "Job not finished yet")
    path = Path(job["filepath"])
    if not path.exists():
        raise HTTPException(410, "File no longer available")
    return FileResponse(path, filename=path.name)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "auth": config.AUTH_ENABLED}
