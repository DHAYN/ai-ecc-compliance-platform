# AI ECC Compliance Platform (PoC)

A small, portfolio-grade Proof of Concept that demonstrates AI-assisted
compliance auditing and access-control automation against Saudi Arabia's
**NCA Essential Cybersecurity Controls (ECC-1:2018)** framework.

Built as a Cybersecurity CO-OP project to show how a compliance workflow —
policy review, gap detection, and HR-driven access revocation — can be
modeled end-to-end with a clean, testable API.

> **This is a demo, not a compliance tool.** Every control definition, employee
> record, and sample policy in this repo is synthetic and written for this
> project. See [Security & Data Policy](#security--data-policy) below.

## Features

- **`POST /api/audit`** — scores a policy text against a given NCA ECC control
  id, returning a compliance score, status, detected gaps, and recommendations.
- **`POST /webhook/revoke`** — NCA ECC **1-9-5** automation: when an employee's
  status changes to `Terminated`, their access is revoked immediately.
- **`GET /api/dashboard`** — aggregates audit results across the seeded sample
  policies plus the HR access-revocation control into one overall compliance
  percentage.

## Architecture

```
                        ┌─────────────────────────┐
                        │        Client / UI       │
                        │ (curl, Swagger UI, etc.) │
                        └────────────┬─────────────┘
                                     │ HTTP (JSON)
                                     ▼
                        ┌─────────────────────────┐
                        │      app/main.py          │
                        │   FastAPI route layer     │
                        │  /api/audit                │
                        │  /webhook/revoke           │
                        │  /api/dashboard            │
                        └──────┬──────────────┬─────┘
                               │              │
                 ┌─────────────┘              └─────────────┐
                 ▼                                           ▼
   ┌───────────────────────────┐               ┌───────────────────────────┐
   │ app/services/ai_auditor.py │               │ app/services/automation.py │
   │                             │               │                             │
   │  AuditorBackend (interface) │               │  process_employee_status()  │
   │   ├─ MockKeywordAuditor      │              │  compute_hr_control_        │
   │   │   (default, rule-based)  │              │    compliance()             │
   │   └─ LLMAuditor               │              │                             │
   │       (swap-in via           │               │  NCA ECC 1-9-5:             │
   │        AI_AUDITOR_API_KEY)   │               │  revoke access on           │
   │                             │               │  termination                 │
   └──────────────┬──────────────┘               └──────────────┬──────────────┘
                  │                                              │
                  ▼                                              ▼
   ┌───────────────────────────┐               ┌───────────────────────────┐
   │  data/ecc_framework.json    │               │  data/user_database.json    │
   │  (synthetic controls:       │               │  (3 synthetic employees)     │
   │   1-1, 1-9 / 1-9-5, 2-3)     │               │                             │
   └───────────────────────────┘               └───────────────────────────┘
                  ▲
                  │ audited against
                  │
   ┌───────────────────────────┐
   │  data/samples/*.txt          │
   │  fake Wi-Fi policy, fake NDA  │
   └───────────────────────────┘
```

The AI auditor is isolated behind the `AuditorBackend` interface so the mock
(keyword-based) implementation can be swapped for a real LLM call later
without touching any route code — see
[app/services/ai_auditor.py](app/services/ai_auditor.py).

## NCA ECC control mapping

| Control ID | Domain                    | Title                              | How it's exercised in this PoC                                    |
|------------|---------------------------|-------------------------------------|--------------------------------------------------------------------|
| **1-1**    | Cybersecurity Governance  | Cybersecurity Strategy              | `POST /api/audit` scores free-text policy against required elements (strategy, review cadence, approval). |
| **1-9**    | Cybersecurity Governance  | Human Resources Cybersecurity       | `POST /api/audit` against the sample NDA (confidentiality, background checks, security awareness). |
| **1-9-5**  | Cybersecurity Governance  | Termination / Change of Employment  | `POST /webhook/revoke` automatically revokes access when an employee's status becomes `Terminated`; also audited as a policy-text sub-control. |
| **2-3**    | Cybersecurity Defense     | Wireless & Network Access Security  | `POST /api/audit` against the sample Wi-Fi policy (encryption, guest network segmentation, password rotation, monitoring). |

`GET /api/dashboard` rolls all four of the above up into a single
`overall_compliance_percentage`.

> Control text in `data/ecc_framework.json` is a simplified, illustrative
> representation for demo purposes — not verbatim NCA documentation.

## Security & data policy

This project **only ever processes synthetic sample data**:

- `data/ecc_framework.json` — hand-written, simplified ECC control definitions.
- `data/user_database.json` — 3 fictional employee records.
- `data/samples/*.txt` — a fake Wi-Fi policy and a fake NDA, written for this repo.

It must never be pointed at a real organization's policies, HR export, or
credentials. See [CLAUDE.md](CLAUDE.md) for the full constraint as enforced
during development.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` for interactive Swagger docs.

### Example requests

```bash
# Audit the sample Wi-Fi policy against control 2-3
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d "{\"policy_text\": \"$(cat data/samples/wifi_policy.txt)\", \"ecc_control_id\": \"2-3\"}"

# Revoke access for a terminated employee (NCA ECC 1-9-5)
curl -X POST http://127.0.0.1:8000/webhook/revoke \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "EMP003", "status": "Terminated"}'

# Overall compliance dashboard
curl http://127.0.0.1:8000/api/dashboard
```

## Running tests

```bash
pytest
```

The suite covers all three endpoints, including error cases (unknown ECC
control, unknown employee, invalid status, and validation errors). Tests that
exercise `/webhook/revoke` run against an isolated temp copy of
`data/user_database.json` (see `tests/conftest.py`) so the committed seed data
is never mutated by a test run.

## Swapping in a real LLM auditor

`app/services/ai_auditor.py` exposes `get_auditor()`, which returns the
built-in `MockKeywordAuditor` by default. Setting the `AI_AUDITOR_API_KEY`
environment variable switches to the `LLMAuditor` extension point — implement
a prompt there against your provider of choice, returning the same
`{compliance_score, status, detected_gaps, recommendations}` schema, and no
route or test code needs to change.

## Tech stack

- **Python 3.11+**
- **FastAPI** + **Pydantic** for the API layer and request validation
- **pytest** + **httpx**/`TestClient` for the test suite
- Deployable to **Render** via `render.yaml`

## Project layout

```
app/
  main.py                    FastAPI app, route wiring
  services/
    ai_auditor.py             Compliance audit engine (mock now, LLM-ready)
    automation.py             NCA ECC 1-9-5 access-revocation automation
data/
  ecc_framework.json           Synthetic ECC control definitions
  user_database.json            Synthetic employee records
  samples/                       Synthetic sample policy texts
tests/                              pytest suite
```
