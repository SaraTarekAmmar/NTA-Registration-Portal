# Active Task

> Agent protocol: read this file at the START of every turn. Keep it current as you work.
> Work is NOT done until every box below is ticked AND the changes are pushed to GitHub.

## Goal
Verify the authentication and dashboard flows for the Admin, Editor, and Coordinator portals using browser automation.

## Context / Constraints
- Credentials:
  - Admin: admin@nta.edu.eg / 29001011234567 / NTA@Admin2026 (Port 8002)
  - Editor: editor@nta.edu.eg / 29505051234567 / NTA@Editor2026 (Port 8004)
  - Coordinator: coordinator@nta.edu.eg / 29304041234567 / NTA@Coord2026 (Port 8005)
- Use `browser_subagent` or programmatic execution (due to browser issues) to test the login flows, check for successful redirects to dashboards, and ensure no console/render errors occur.

## Checklist
- [x] Test Coordinator login and dashboard flow (Port 8005)
- [x] Test Editor login and dashboard flow (Port 8004)
- [x] Test Admin login and dashboard flow (Port 8002)

## Next step
Verify the changes, commit, and push.
