# MEGA Loop Test Agent

Small intentionally simple Python project for testing MEGA Loop code connection,
bug detection, auto-fix, and pull request generation.

## What this repo contains

- A tiny support-ticket classifier in `src/agent.py`
- A known runtime bug for invalid priority values
- Pytest tests that document the expected behavior

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest
```

## Intended test bug

`classify_ticket()` assumes every ticket priority is one of:

- `low`
- `medium`
- `high`
- `urgent`

Unknown priorities currently raise a `KeyError`. A robust fix should handle
unknown or missing priority values without crashing.
