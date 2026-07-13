"""Tests for GET /api/dashboard."""
from __future__ import annotations


def test_dashboard_returns_overall_compliance_percentage(client):
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()

    assert "overall_compliance_percentage" in body
    assert 0 <= body["overall_compliance_percentage"] <= 100

    assert isinstance(body["controls"], list)
    assert len(body["controls"]) == 3

    control_ids = {c["control_id"] for c in body["controls"]}
    assert control_ids == {"2-3", "1-9", "1-9-5"}

    for control in body["controls"]:
        assert 0 <= control["compliance_score"] <= 100
        assert control["status"] in {"Compliant", "Gap"}
