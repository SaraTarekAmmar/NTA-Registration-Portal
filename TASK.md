# Active Task

> Agent protocol: read this file at the START of every turn. Keep it current as you work.
> Work is NOT done until every box below is ticked AND the changes are pushed to GitHub.

## Goal
Fix light mode styling for the builder action bar and timeline numbers on the admission builder page.

## Context / Constraints
- Action bar and timeline numbers remained dark/black even when light mode was toggled on.
- Override backgrounds and borders in `html.light-mode` to match the light theme cleanly.

## Checklist
- [x] Identify the dark elements (action bar, timeline numbers, connectors) in `editor-admission-builder.html`
- [x] Add CSS overrides under `html.light-mode`
- [x] Verify layout changes using the browser subagent in light mode
- [ ] Commit changes
- [ ] Push to GitHub (origin/master)

## Next step
Commit the styles fix and push to GitHub.
