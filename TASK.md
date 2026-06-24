# Active Task

> Agent protocol: read this file at the START of every turn. Keep it current as you work.
> Work is NOT done until every box below is ticked AND the changes are pushed to GitHub.

## Goal
Fix `http://localhost:8005/` returning "Not Found" by re-ordering route registration in the coordinator backend.

## Context / Constraints
- The FastAPI mount point `/` intercepts the root path request when registered before the `@app.get("/")` route.
- Moving `@app.get("/")` before the mount point registration (consistent with admin and editor main.py configurations) fixes the 404 error.

## Checklist
- [x] Move root redirect route before static folder mount in `coordinator/backend/main.py`
- [x] Verify root URL redirect works for coordinator
- [x] Restart coordinator server and confirm fix

## Next step
None. The redirect works perfectly.
