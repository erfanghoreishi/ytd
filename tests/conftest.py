import importlib
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def app_modules(tmp_path: Path, monkeypatch):
    """Reload app modules with isolated tmp dirs and chosen auth env."""
    monkeypatch.setenv("YTD_DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("YTD_DATA_DIR", str(tmp_path / "data"))

    def reload(auth: bool = False, user: str = "admin", pass_hash: str = ""):
        monkeypatch.setenv("YTD_AUTH_ENABLED", "true" if auth else "false")
        monkeypatch.setenv("YTD_USER", user)
        monkeypatch.setenv("YTD_PASS_HASH", pass_hash)
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                sys.modules.pop(name, None)
        return importlib.import_module("app.main")

    return reload
