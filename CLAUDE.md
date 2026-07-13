# CLAUDE.md

Guidance for Claude Code (and any AI assistant) working in this repository.

## Project

An AI-powered Proof of Concept that demonstrates automated compliance auditing
and access-control automation against Saudi Arabia's NCA Essential Cybersecurity
Controls (ECC) framework. Built by a Cybersecurity CO-OP trainee as a portfolio
project — the goal is clean, explainable, well-tested code that reads well in a
code review, not a production system.

## Critical security constraint — read this first

**This project must NEVER process real confidential organizational policies,
credentials, or personal data.** It only ever operates on synthetic, self-seeded
sample data.

- All policy text, employee records, and framework data live in `data/` and are
  fabricated by the project maintainer for demo purposes.
- Never accept, request, or wire up a path/upload mechanism for a real company's
  policy documents, HR export, or credentials.
- Never add integrations (email, ticketing, IdP/SCIM, SIEM, etc.) that would let
  this PoC touch a real production system. Anything like that stays firmly
  out of scope.
- If asked to add a feature that would require real organizational data to be
  useful, push back and suggest a synthetic-data equivalent instead.
- Sample employee names, IDs, and policy text are fictional. Keep it that way
  when adding new seed data.

## Stack & conventions

- **Language/framework:** Python 3.11+, FastAPI, pytest.
- **Style:** clean, modular, well-commented where the *why* isn't obvious from
  the code. Prefer small, single-responsibility modules over clever abstractions.
- **AI logic is isolated behind an interface.** `app/services/ai_auditor.py`
  ships a rule/keyword-based mock auditor by default. A real LLM backend can be
  swapped in later via an env var (`AI_AUDITOR_API_KEY`) without changing the
  API contract — don't collapse that interface for convenience.
- **Data files are the source of truth for seed content**: `data/ecc_framework.json`,
  `data/user_database.json`, `data/samples/*.txt`. Treat the ECC control text in
  this repo as a simplified, illustrative representation for demo purposes —
  not a verbatim reproduction of the official NCA document.

## Project layout

```
app/
  main.py                 FastAPI app, route wiring
  services/
    ai_auditor.py          Compliance audit engine (mock now, LLM-ready interface)
    automation.py          NCA ECC 1-9-5 access-revocation automation
data/
  ecc_framework.json        Synthetic ECC control definitions (1-1, 1-9/1-9-5, 2-3)
  user_database.json         Synthetic employee records
  samples/                    Synthetic sample policy texts (Wi-Fi, NDA)
tests/                          pytest suite covering all endpoints incl. error cases
```

## Workflow expectations

- **Always run the full pytest suite before opening or updating a PR.** A PR
  with failing tests is not ready.
- When changing `data/user_database.json` on disk as a side effect (the revoke
  webhook does this), tests must isolate against a temp copy — never let a test
  run mutate the committed seed file.
- Keep `requirements.txt` minimal; anything needed only for the optional real-LLM
  path should be noted in a comment rather than pulled in as a hard dependency.
- Update `README.md`'s architecture diagram and ECC mapping table when the
  structure or control coverage changes.
