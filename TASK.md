# Active Task

> Agent protocol: read this file at the START of every turn. Keep it current as you work.
> Work is NOT done until every box below is ticked AND the changes are pushed to GitHub.
> Replace the example below with the real task whenever a new one starts.

## Goal
Find why the admin, editor, and coordinator Windows batch launchers appear not to run, and fix any broken startup configuration.

## Context / Constraints
- `admin/RUN_ADMIN.bat`, `editor/RUN_EDITOR.bat`, and `coordinator/RUN_COORDINATOR.bat` are the startup scripts.
- Editor launcher had a port mismatch with the rest of the repo and with superadmin.
- Keep changes aligned with the repo's existing no-bundler, FastAPI, Windows batch setup.

## Checklist
- [x] Inspect the batch launchers and backend startup files
- [x] Identify the startup mismatch
- [x] Fix the editor port configuration
- [x] Verify the updated editor launcher starts on port 8004
- [x] Commit changes
- [x] Push to GitHub (origin/master)

## Next step
Commit the launcher fix and push it to origin.

## Notes / Log
- 2026-06-23 — Confirmed admin and coordinator launch successfully; editor was wired to port 8003, conflicting with superadmin. Updated editor startup to 8004.
- 2026-06-23 — Committed as `aa83b52` and pushed to `origin/master`.

---
<!-- EXAMPLE (delete when starting a real task):
## Goal
Add CSV export to the admin trainees page.

## Checklist
- [x] Add /api/admin/trainees/export route
- [ ] Add "Export CSV" button to admin/trainees.html
- [ ] Test download with seeded data
- [ ] Commit changes
- [ ] Push to GitHub (origin/master)

## Next step
Wire the export button click to fetch the new endpoint.
-->
