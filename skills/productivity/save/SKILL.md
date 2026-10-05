---
name: save
description: Save current session state to .scratch/CONTINUE.md and prepare for a safe user-controlled exit.
disable-model-invocation: true
---

# Save Session

Create one concise, decision-dense checkpoint that `/load` can resume later.

<constraints>

- Act only when the user explicitly invokes `/save`.
- Use `.scratch/CONTINUE.md` as the only active checkpoint path. Never write a root-level `CONTINUE.md`.
- Never terminate the host process or run `kill`. The user controls when the session exits.
- Omit secrets, credentials, private keys, cookies, `.env` values, and raw logs. Record safe summaries instead.
- Distinguish verified facts from assumptions. Never claim a check passed unless it ran successfully.

</constraints>

## Workflow

1. Create `.scratch/` if needed.
2. If `.scratch/CONTINUE.md` exists, read it before replacing it. Carry forward only unresolved information still supported by the current conversation or repository. Current verified state wins.
3. Capture repository state when the workspace is a Git repository:
   - Working directory
   - Branch
   - HEAD commit
   - Concise working-tree status
4. Write `.scratch/CONTINUE.md` with this structure:

```markdown
# Session Handoff

Generated: <ISO 8601 timestamp>

## Goal
<The outcome the user wants>

## User Requirements and Corrections
- <Constraints, preferences, and corrections that must survive>

## Current State
### Completed
- <Verified result>

### In Progress
- <Incomplete work and its exact stopping point>

## Decisions and Rationale
- <Decision>: <reason>

## Blockers and Open Questions
- <Blocker or question, or "None">

## Files in Play
- `<path>`: <why it matters>

## Verification
- <Command or check>: <result, or not run>

## Repository Snapshot
- Working directory: `<path>`
- Branch: `<branch or not applicable>`
- HEAD: `<commit or not applicable>`
- Working tree: <concise status>

## Next Actions
1. <First concrete action>
2. <Second action>
3. <Third action>

## Resume
Invoke `/load` to reconcile this checkpoint with the workspace and continue.
```

5. Verify that the file exists, contains no placeholders, and names a concrete first action.
6. Report exactly what happened without continuing the work:

```text
Checkpoint saved: .scratch/CONTINUE.md
Use /exit to close this session. Invoke /load later to continue.
```
