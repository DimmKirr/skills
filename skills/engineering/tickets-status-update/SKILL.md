---
name: tickets-status-update
description: Post a structured status update comment (DONE / WORKING ON / BLOCKED ON) to the current ticket in Linear/Jira.
argument-hint: "[ticket-id]"
disable-model-invocation: true
---

# Ticket Update

> **Tool Binding:** This skill uses abstract ticketing operations (`pm.*`). See [tools/README.md](tools/README.md) for the interface and tool-specific bindings (Linear, Jira).

Post a status update comment on a ticket summarizing the current session's progress: what is confirmed done, what is actively being worked on, and what is blocked.

**This skill reports status; it never changes it.** The only write it performs is the single `pm.add_comment` call. No code edits, no state-changing commands, no ticket field changes: gaps, failures, and blockers get reported in the comment, not fixed.

## Steps

1. **Identify the target ticket**
   - Ticket ID passed as argument (`/tickets-status-update PROJ-123`) wins.
   - Otherwise extract a ticket ID from the current branch name (`git branch --show-current`).
   - Otherwise use the ticket being discussed or worked on in this conversation.
   - If none found, or more than one candidate: ask the user which ticket to update.
   - Resolve it with `pm.get_ticket` to get the canonical `identifier` and `url`.

2. **Gather status from session context** (read-only)
   - Use the session transcript plus read-only commands only (`git branch`, `git log`, `git status`, `git diff`). Never run builds, tests, installs, or fixes to upgrade an item's section: evidence either already exists in the session, or the item is WORKING ON.
   - Group the session's work into **strategic goals**. A strategic goal is an outcome-level objective (e.g. "Make api-proxy boot with Postgres 16"), not a file-level chore. Use the ticket's own goals as the primary frame.
   - Classify each goal into exactly one section:
     - **DONE**: confirmed working with evidence from this session (test run, build output, observed behavior). Unverified work is NOT done; it goes under WORKING ON.
     - **WORKING ON**: actively in progress, viable path forward exists.
     - **BLOCKED ON**: attempts exhausted, or the current approach is believed impossible without outside help or a decision.

3. **Compose the comment** using the exact format below.
   - Omit any section that has no items. Never post empty scaffolding.
   - Every summary line is one sentence.
   - Observed results quote concrete output (error text, command result), not a paraphrase.

4. **Post and report**
   - Post the comment via `pm.add_comment`.
   - Report back to the user: ticket identifier, full URL, and the sections posted.

## Comment Format

```markdown
DONE:
1. <TaskName>
   1.1. Confirmed: <one sentence: what is confirmed working and how it was verified>
   1.2. Before: <one sentence: the state before this work and why it needed doing>
   1.3. After: <one sentence: the state after this work and how it moves toward the goal>
2. <next done goal, same sub-structure>

WORKING ON:
1. <TaskName>
   1.1. Currently: <one sentence: what is being worked on right now>
   1.2. Tactical Goal: <one sentence: the immediate objective that serves the strategic goal>
2. <next active goal, same sub-structure>

BLOCKED ON:
1. <TaskName>
   1.1. Blocker: <BlockerTitle>. <one-sentence description of the blocker>
   1.2. Attempts Made:
      1.2.1. <attempt: one short sentence of what was tried>
         - Expected Result: <what this attempt was expected to produce>
         - Observed Result: <the concrete result that constitutes the block, e.g. the exact error>
         - Criticality Assessment: <one sentence: how critical this step is to the goal>
         - Potential Alternatives: P(<alternative 1> works)=<0..1>, P(<alternative 2> works)=<0..1>
      1.2.2. <next attempt, same sub-structure>
2. <next blocked goal, same sub-structure>
```

`<TaskName>` is the strategic goal name in all three sections. The same goal may appear in only one section per update.

## Example

```markdown
DONE:
1. Make api-proxy boot with Postgres 16
   1.1. Confirmed: `task dev` starts the service and `/healthz` returns 200 against postgres:16.
   1.2. Before: startup crashed because migration 0042 used the removed `pg_stat_activity.procpid` column, pinning local dev to Postgres 12.
   1.3. After: migration 0042 uses `pid` and compose pins postgres:16, so dev now matches the production major version.

WORKING ON:
1. Migrate CI pipeline to Postgres 16
   1.1. Currently: updating the GitHub Actions service container and integration test fixtures.
   1.2. Tactical Goal: get the integration suite green on postgres:16 so the version bump can merge.

BLOCKED ON:
1. Restore python2 build step on edge nixpkgs
   1.1. Blocker: python2 removed upstream. The `python2` attribute no longer exists in nixpkgs-unstable, so the legacy asset pipeline cannot build.
   1.2. Attempts Made:
      1.2.1. Installed python2 from edge nixpkgs via `nix profile install nixpkgs#python2`.
         - Expected Result: python2 binary on PATH for the legacy build script.
         - Observed Result: `error: attribute 'python2' missing`; python2 was removed from the store.
         - Criticality Assessment: critical, the asset pipeline has no python3 port so this blocks the entire legacy build.
         - Potential Alternatives: P(pinning nixpkgs 22.11 for this one derivation works)=0.7, P(porting the script to python3 works)=0.5, P(vendoring a prebuilt python2 works)=0.2
```

## Scope Guard: Report, Do Not Fix

This skill is a snapshot camera, not a repair tool. Its value is an accurate picture of the current state, including the ugly parts. If any of these thoughts appear while running it, stop and keep composing the comment:

| Temptation | Correct action |
|------------|----------------|
| "This blocker is actually a one-line fix, let me apply it first" | Report it under BLOCKED ON (or WORKING ON) and list the fix as a Potential Alternative; fixing happens after this skill ends, on user request |
| "Let me quickly run the tests so I can mark this DONE" | Do not start new runs; no existing session evidence means WORKING ON |
| "I'll finish the last WORKING ON item, then post a nicer update" | Post the honest snapshot of the state as it is now |
| "I noticed an unrelated bug while gathering" | Mention it in the comment if relevant to the ticket; never touch code |
| "The update would look better if more were DONE" | The comment's value is accuracy, not completeness |

A status update that says "blocked" or "in progress" is a successful run of this skill. After posting, return control to the user: suggest next steps in your reply if useful, but take none of them.

## Rules

- **Report, never fix.** No file edits, no code, no state-changing commands, no new builds/tests/installs while this skill runs. The single `pm.add_comment` call is the only write this skill performs.
- **Comment only.** Never change ticket status, assignee, labels, or description. Status transitions and grooming are the `/pm` skill's job.
- **Evidence before DONE.** A goal is DONE only if this session verified it (command output, passing test, observed behavior). Otherwise it is WORKING ON.
- **Stable goal names.** Reuse the same `<TaskName>` wording across successive updates on the same ticket so consecutive comments are comparable.
- **Honest probabilities.** Alternative estimates reflect real confidence, not optimism; it is fine to list P(x works)=0.1.
- **One ticket per invocation.** If the session spans multiple tickets, ask which one to update (or run the skill once per ticket on request).
- **No secrets.** Never paste tokens, credentials, or private URLs into the comment; redact them from quoted output.
