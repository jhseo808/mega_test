# MEGA Loop Seed Bug Scenarios

This repository intentionally contains a reproducible routing bug for MEGA Loop beta testing.

## Grouping target

`src/agent.py` raises `KeyError` when a support ticket uses a priority that is not present in `PRIORITY_WEIGHTS`.

Known failing inputs:

- `priority="critical"`
- `priority="vip_critical"`
- `priority="sev1"`
- missing `priority`

All of these should point to the same root cause:

```python
score = PRIORITY_WEIGHTS[priority]
```

Expected fix:

- handle unknown or missing priorities without crashing
- route critical incident-like tickets to `escalate`
- keep existing low and urgent ticket behavior unchanged

## Baseline passing inputs

- low priority standard customer -> `low_touch`
- urgent enterprise outage -> `escalate`
