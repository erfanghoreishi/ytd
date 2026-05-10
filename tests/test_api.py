from fastapi.testclient import TestClient


def test_healthz_open_when_auth_disabled(app_modules):
    main = app_modules(auth=False)
    client = TestClient(main.app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "auth": False}


def test_index_renders(app_modules):
    main = app_modules(auth=False)
    client = TestClient(main.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "YTD" in r.text


def test_create_job_queues_background_task(app_modules, monkeypatch):
    main = app_modules(auth=False)
    calls = []
    monkeypatch.setattr(main.downloader, "run_job", lambda jid, url: calls.append((jid, url)))
    client = TestClient(main.app)

    r = client.post("/jobs", data={"url": "https://example.com/abc"})
    assert r.status_code == 200
    assert "https://example.com/abc" in r.text

    jobs = main.db.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["url"] == "https://example.com/abc"
    assert calls == [(jobs[0]["id"], "https://example.com/abc")]


def test_create_job_rejects_blank(app_modules):
    main = app_modules(auth=False)
    client = TestClient(main.app)
    r = client.post("/jobs", data={"url": "   "})
    assert r.status_code == 400


def test_file_endpoint_404_when_unfinished(app_modules):
    main = app_modules(auth=False)
    client = TestClient(main.app)
    job_id = main.db.create_job("https://x")
    r = client.get(f"/jobs/{job_id}/file")
    assert r.status_code == 409


def test_auth_required_when_enabled(app_modules):
    from app.auth import hash_password
    h = hash_password("s3cret")
    main = app_modules(auth=True, user="alice", pass_hash=h)
    client = TestClient(main.app)

    assert client.get("/").status_code == 401
    assert client.get("/", auth=("alice", "wrong")).status_code == 401
    assert client.get("/", auth=("alice", "s3cret")).status_code == 200


def test_downloader_progress_hook_updates_db(app_modules):
    main = app_modules(auth=False)
    job_id = main.db.create_job("https://x")
    opts = main.downloader._build_opts(job_id)
    hook = opts["progress_hooks"][0]
    hook({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})
    j = main.db.get_job(job_id)
    assert j["status"] == "downloading"
    assert j["progress"] == 50.0
    hook({"status": "finished"})
    assert main.db.get_job(job_id)["status"] == "processing"
