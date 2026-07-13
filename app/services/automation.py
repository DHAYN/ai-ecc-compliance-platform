"""Automation for NCA ECC control 1-9-5: revoke system access immediately
upon an employee's termination or change of employment.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
USER_DB_PATH = DATA_DIR / "user_database.json"

TERMINATED_STATUS = "Terminated"


class EmployeeNotFoundError(KeyError):
    """Raised when the employee_id isn't in the user database."""


def _load_db(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(path: Path, db: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
        f.write("\n")


def process_employee_status(
    employee_id: str,
    status: str,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Update an employee's status and, per NCA ECC 1-9-5, revoke access
    immediately if the new status is "Terminated". Returns a summary dict
    including the resulting control-compliance status.

    db_path defaults to the module-level USER_DB_PATH, looked up at call
    time (not bind time) so tests can monkeypatch it to a temp file and
    never mutate the committed seed data.
    """
    path = db_path if db_path is not None else USER_DB_PATH
    db = _load_db(path)
    employee = next(
        (e for e in db["employees"] if e["employee_id"] == employee_id), None
    )
    if employee is None:
        raise EmployeeNotFoundError(employee_id)

    employee["status"] = status
    if status == TERMINATED_STATUS:
        employee["access_revoked"] = True
        control_status = "Compliant"
    else:
        control_status = "Not Applicable"

    _save_db(path, db)

    return {
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "status": employee["status"],
        "access_revoked": employee["access_revoked"],
        "nca_control_1_9_5": control_status,
    }


def compute_hr_control_compliance(db_path: Path | None = None) -> dict[str, Any]:
    """Aggregate view used by the dashboard: what fraction of terminated
    employees currently have their access revoked, per NCA ECC 1-9-5.

    db_path defaults to USER_DB_PATH looked up at call time -- see the note
    in process_employee_status for why that matters for test isolation.
    """
    path = db_path if db_path is not None else USER_DB_PATH
    db = _load_db(path)
    terminated = [e for e in db["employees"] if e["status"] == TERMINATED_STATUS]

    if not terminated:
        return {"control_id": "1-9-5", "compliance_percentage": 100, "sample_size": 0}

    revoked = sum(1 for e in terminated if e["access_revoked"])
    percentage = round((revoked / len(terminated)) * 100)
    return {
        "control_id": "1-9-5",
        "compliance_percentage": percentage,
        "sample_size": len(terminated),
    }
