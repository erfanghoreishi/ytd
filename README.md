# YTD — Minimal YouTube Download Manager

A small open-source web app that wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) in a FastAPI UI.
One Docker image, two deployment modes: run it locally, or run it on an Ubuntu server with nginx + basic auth in front.

- **Backend:** FastAPI + uvicorn
- **Downloader:** yt-dlp + ffmpeg
- **UI:** Jinja2 + HTMX (zero JS build)
- **Storage:** SQLite + a `downloads/` folder
- **Auth:** HTTP Basic, env-gated, single user
- **Container:** `python:3.12-slim`
- **CI/CD:** GitHub Actions → GHCR → SSH deploy

## Local install (one minute)

Requires Docker.

```bash
git clone https://github.com/<you>/ytd && cd ytd
cp .env.example .env
docker compose up
```

Open http://localhost:8000. Downloads land in `./downloads/`.

To run without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Run the tests

```bash
pip install -e ".[dev]"
pytest -q
```

## Server deployment (Ubuntu + Docker)

### One-time setup

1. Provision an Ubuntu VPS, install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER && newgrp docker
   ```
2. Clone the repo to `/srv/ytd` and create the production `.env`:
   ```bash
   sudo mkdir -p /srv/ytd && sudo chown $USER /srv/ytd
   git clone https://github.com/<you>/ytd /srv/ytd && cd /srv/ytd
   cp .env.example .env
   ```
3. Edit `/srv/ytd/.env`:
   ```env
   YTD_AUTH_ENABLED=true
   YTD_USER=you
   YTD_PASS_HASH=<bcrypt hash — see below>
   YTD_IMAGE=ghcr.io/<you>/ytd:latest
   ```
   Generate the password hash:
   ```bash
   docker run --rm python:3.12-slim sh -c "pip install -q passlib[bcrypt] && python -c 'from passlib.hash import bcrypt; print(bcrypt.hash(\"your-password\"))'"
   ```
4. Log Docker into GHCR (so the server can pull the image):
   ```bash
   echo $GHCR_PAT | docker login ghcr.io -u <you> --password-stdin
   ```

### Every deploy

CI handles it on push to `main`. To deploy by hand:

```bash
ssh you@SERVER_IP
cd /srv/ytd && bash deploy/deploy.sh
```

Open http://SERVER_IP/. nginx prompts for the basic-auth user.

### CI/CD secrets

Set these in the GitHub repo (Settings → Secrets → Actions):

| Secret        | Value                                          |
|---------------|------------------------------------------------|
| `DEPLOY_HOST` | server IP / hostname                           |
| `DEPLOY_USER` | SSH user (same one that owns `/srv/ytd`)       |
| `DEPLOY_KEY`  | private SSH key authorized on the server       |

The image is pushed to GHCR using the workflow's built-in `GITHUB_TOKEN` — no extra secret needed.

## Layout

```
app/                FastAPI app (main, auth, downloader, db, templates)
tests/              pytest suite (yt-dlp mocked)
deploy/             nginx.conf, deploy.sh
Dockerfile          python:3.12-slim + ffmpeg
docker-compose.yml         local: ytd container, port 8000
docker-compose.prod.yml    server overlay: adds nginx, drops port
.github/workflows/  ci.yml + deploy.yml
```

## Disclaimer

For personal/educational use. Respect YouTube's Terms of Service and the rights of content creators.
