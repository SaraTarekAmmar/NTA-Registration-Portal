# Browser E2E tests

These tests use Python Playwright and are intentionally opt-in because they need running Admin and Editor backends plus a seeded database.

## Install

```bash
python -m pip install pytest playwright
python -m playwright install chromium
```

## Run

Set `NTA_E2E=1`, point `NTA_ADMIN_BASE_URL` and `NTA_EDITOR_BASE_URL` at running portals, and provide the required `NTA_ADMIN_*` and `NTA_EDITOR_*` login environment variables.

The course create/publish/material/session mutation test is skipped unless `NTA_E2E_ALLOW_MUTATION=1` is set.

```bash
pytest -q tests/e2e
```
