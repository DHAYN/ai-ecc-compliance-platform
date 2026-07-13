"""Tests for POST /webhook/revoke (NCA ECC 1-9-5 automation)."""
from __future__ import annotations

import json


def test_revoke_on_termination_marks_access_revoked(client, isolated_user_db):
    response = client.post(
        "/webhook/revoke", json={"employee_id": "EMP003", "status": "Terminated"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == "EMP003"
    assert body["status"] == "Terminated"
    assert body["access_revoked"] is True
    assert body["nca_control_1_9_5"] == "Compliant"

    persisted = json.loads(isolated_user_db.read_text(encoding="utf-8"))
    employee = next(
        e for e in persisted["employees"] if e["employee_id"] == "EMP003"
    )
    assert employee["access_revoked"] is True
    assert employee["status"] == "Terminated"


def test_revoke_active_status_does_not_revoke_access(client, isolated_user_db):
    response = client.post(
        "/webhook/revoke", json={"employee_id": "EMP001", "status": "Active"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_revoked"] is False
    assert body["nca_control_1_9_5"] == "Not Applicable"


def test_revoke_unknown_employee_returns_404(client, isolated_user_db):
    response = client.post(
        "/webhook/revoke", json={"employee_id": "EMP999", "status": "Terminated"}
    )

    assert response.status_code == 404


def test_revoke_invalid_status_returns_422(client, isolated_user_db):
    response = client.post(
        "/webhook/revoke", json={"employee_id": "EMP001", "status": "Fired"}
    )

    assert response.status_code == 422


def test_revoke_missing_field_returns_422(client, isolated_user_db):
    response = client.post("/webhook/revoke", json={"status": "Terminated"})

    assert response.status_code == 422
