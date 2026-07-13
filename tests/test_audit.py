"""Tests for POST /api/audit."""
from __future__ import annotations

from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def _read_sample(name: str) -> str:
    return (SAMPLES_DIR / name).read_text(encoding="utf-8")


def test_audit_wifi_policy_against_2_3_detects_partial_gaps(client):
    policy_text = _read_sample("wifi_policy.txt")

    response = client.post(
        "/api/audit", json={"policy_text": policy_text, "ecc_control_id": "2-3"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ecc_control_id"] == "2-3"
    assert 0 <= body["compliance_score"] <= 100
    assert body["status"] in {"Compliant", "Gap"}
    assert isinstance(body["detected_gaps"], list)
    assert isinstance(body["recommendations"], list)
    # The sample Wi-Fi policy covers encryption + guest network but omits
    # password rotation and monitoring -> should surface as gaps.
    assert body["status"] == "Gap"
    assert any("password rotation" in gap.lower() for gap in body["detected_gaps"])
    assert len(body["recommendations"]) == len(body["detected_gaps"])


def test_audit_nda_against_1_9_5_detects_partial_gaps(client):
    policy_text = _read_sample("nda_policy.txt")

    response = client.post(
        "/api/audit", json={"policy_text": policy_text, "ecc_control_id": "1-9-5"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ecc_control_id"] == "1-9-5"
    # The sample NDA covers "return of property" but never mentions
    # revoking access or an immediate timeframe -> should not be compliant.
    assert body["status"] == "Gap"
    assert any("revocation" in gap.lower() for gap in body["detected_gaps"])


def test_audit_fully_covered_policy_is_compliant(client):
    policy_text = (
        "Our approved cybersecurity strategy is reviewed annually. "
        "This policy was approved by the CISO."
    )

    response = client.post(
        "/api/audit", json={"policy_text": policy_text, "ecc_control_id": "1-1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["compliance_score"] == 100
    assert body["status"] == "Compliant"
    assert body["detected_gaps"] == []
    assert body["recommendations"] == []


def test_audit_unknown_control_returns_404(client):
    response = client.post(
        "/api/audit", json={"policy_text": "irrelevant text", "ecc_control_id": "9-9-9"}
    )

    assert response.status_code == 404


def test_audit_empty_policy_text_returns_422(client):
    response = client.post(
        "/api/audit", json={"policy_text": "", "ecc_control_id": "1-1"}
    )

    assert response.status_code == 422


def test_audit_missing_field_returns_422(client):
    response = client.post("/api/audit", json={"policy_text": "some text"})

    assert response.status_code == 422
