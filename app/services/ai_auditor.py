"""AI compliance auditor: scores policy text against an NCA ECC control.

Ships with a rule/keyword-based mock backend so the PoC runs deterministically
with zero external dependencies or API keys. A real LLM backend can be swapped
in later by setting AI_AUDITOR_API_KEY -- get_auditor() picks the backend, and
the FastAPI layer never needs to know which one is active.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
ECC_FRAMEWORK_PATH = DATA_DIR / "ecc_framework.json"

COMPLIANCE_THRESHOLD = 70


class ControlNotFoundError(KeyError):
    """Raised when the requested ECC control id isn't in the framework."""


def _load_framework(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_controls(framework: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index every control and subcontrol by its control_id, so callers can
    look up e.g. "1-9-5" as easily as the top-level "1-9"."""
    flat: dict[str, dict[str, Any]] = {}
    for control in framework["controls"]:
        flat[control["control_id"]] = control
        for sub in control.get("subcontrols", []):
            flat[sub["control_id"]] = sub
    return flat


class AuditorBackend(ABC):
    """Interface every compliance-audit backend must implement, so the API
    layer can swap mock <-> LLM without changing any route code."""

    @abstractmethod
    def audit(self, policy_text: str, ecc_control_id: str) -> dict[str, Any]:
        """Return {"compliance_score", "status", "detected_gaps", "recommendations"}."""
        raise NotImplementedError


class MockKeywordAuditor(AuditorBackend):
    """Rule-based auditor: scores a policy by how many of a control's
    required elements it mentions. Fully deterministic, no network calls --
    good for a PoC and for repeatable tests.
    """

    def __init__(self, framework_path: Path = ECC_FRAMEWORK_PATH) -> None:
        self._framework = _load_framework(framework_path)
        self._controls = _flatten_controls(self._framework)

    def audit(self, policy_text: str, ecc_control_id: str) -> dict[str, Any]:
        control = self._controls.get(ecc_control_id)
        if control is None:
            raise ControlNotFoundError(ecc_control_id)

        elements = control.get("required_elements", [])
        haystack = policy_text.lower()

        detected_gaps: list[str] = []
        recommendations: list[str] = []
        matched = 0

        for element in elements:
            if element["keyword"].lower() in haystack:
                matched += 1
            else:
                detected_gaps.append(element["description"])
                recommendations.append(element["recommendation"])

        total = len(elements)
        score = round((matched / total) * 100) if total else 100
        status = "Compliant" if score >= COMPLIANCE_THRESHOLD else "Gap"

        return {
            "ecc_control_id": ecc_control_id,
            "control_title": control["title"],
            "compliance_score": score,
            "status": status,
            "detected_gaps": detected_gaps,
            "recommendations": recommendations,
        }


class LLMAuditor(AuditorBackend):
    """Extension point for a real LLM-backed auditor.

    Only ever instantiated when AI_AUDITOR_API_KEY is set -- the default
    (mock) path never touches this class, so no test or CI run depends on
    a network call or a real API key.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def audit(self, policy_text: str, ecc_control_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "LLM-backed auditing is not implemented in this PoC. Wire a "
            "prompt (policy_text + the control's description/required "
            "elements) against your LLM provider here, returning the same "
            "schema as MockKeywordAuditor.audit()."
        )


def get_auditor() -> AuditorBackend:
    """Backend selection point: mock by default, LLM if a key is configured."""
    api_key = os.getenv("AI_AUDITOR_API_KEY")
    if api_key:
        return LLMAuditor(api_key)
    return MockKeywordAuditor()
