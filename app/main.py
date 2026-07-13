"""FastAPI entrypoint for the AI-powered NCA ECC compliance PoC.

SECURITY NOTE: this service only ever operates on synthetic sample data
seeded in data/ (see CLAUDE.md). Do not wire real organizational policies,
credentials, or personal data into any endpoint here.
"""
from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_auditor import DATA_DIR, ControlNotFoundError, get_auditor
from app.services.automation import (
    EmployeeNotFoundError,
    compute_hr_control_compliance,
    process_employee_status,
)

app = FastAPI(
    title="AI ECC Compliance Platform (PoC)",
    description="Synthetic-data proof of concept for AI-assisted NCA ECC compliance auditing.",
    version="0.1.0",
)

SAMPLES_DIR = DATA_DIR / "samples"


class AuditRequest(BaseModel):
    policy_text: str = Field(min_length=1, description="Raw text of the policy to audit.")
    ecc_control_id: str = Field(description="NCA ECC control id, e.g. '1-9-5'.")


class RevokeRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    status: Literal["Active", "Terminated", "On Leave"]


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ai-ecc-compliance-platform"}


@app.post("/api/audit")
def audit_policy(request: AuditRequest) -> dict:
    auditor = get_auditor()
    try:
        return auditor.audit(request.policy_text, request.ecc_control_id)
    except ControlNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"ECC control '{request.ecc_control_id}' not found",
        )


@app.post("/webhook/revoke")
def revoke_access(request: RevokeRequest) -> dict:
    try:
        return process_employee_status(request.employee_id, request.status)
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Employee '{request.employee_id}' not found",
        )


@app.get("/api/dashboard")
def dashboard() -> dict:
    auditor = get_auditor()

    wifi_text = (SAMPLES_DIR / "wifi_policy.txt").read_text(encoding="utf-8")
    nda_text = (SAMPLES_DIR / "nda_policy.txt").read_text(encoding="utf-8")

    wifi_result = auditor.audit(wifi_text, "2-3")
    nda_result = auditor.audit(nda_text, "1-9")
    hr_result = compute_hr_control_compliance()

    hr_status = "Compliant" if hr_result["compliance_percentage"] >= 70 else "Gap"

    controls = [
        {
            "control_id": wifi_result["ecc_control_id"],
            "title": wifi_result["control_title"],
            "compliance_score": wifi_result["compliance_score"],
            "status": wifi_result["status"],
        },
        {
            "control_id": nda_result["ecc_control_id"],
            "title": nda_result["control_title"],
            "compliance_score": nda_result["compliance_score"],
            "status": nda_result["status"],
        },
        {
            "control_id": hr_result["control_id"],
            "title": "Termination / Change of Employment",
            "compliance_score": hr_result["compliance_percentage"],
            "status": hr_status,
        },
    ]

    overall = round(sum(c["compliance_score"] for c in controls) / len(controls))

    return {
        "overall_compliance_percentage": overall,
        "controls": controls,
    }
