"""Shared pytest fixtures.

Any test that hits /webhook/revoke mutates the on-disk user database as a
side effect. `isolated_user_db` points app.services.automation at a throwaway
copy so the committed synthetic seed data in data/user_database.json is never
altered by a test run.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import automation

ORIGINAL_USER_DB = Path(__file__).resolve().parent.parent / "data" / "user_database.json"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def isolated_user_db(tmp_path, monkeypatch) -> Path:
    temp_db = tmp_path / "user_database.json"
    shutil.copy(ORIGINAL_USER_DB, temp_db)
    monkeypatch.setattr(automation, "USER_DB_PATH", temp_db)
    return temp_db
