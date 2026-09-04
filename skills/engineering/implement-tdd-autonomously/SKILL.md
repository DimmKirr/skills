---
name: implement-tdd-autonomously
description: Implement the agreed work fully autonomously using strict TDD with judgment-call rules and fail-safes. Auto-detects the right verification mode based on context.
disable-model-invocation: true
---

# Autonomous TDD Implementation

Implement work autonomously using test-driven development. Plan everything upfront, ask all questions ONCE, then execute the entire scope without stopping.

## Step 1: Plan Scope (upfront, ONE pass)

Derive the full scope from the conversation context: tickets, features, fixes, refactors discussed. Build the complete work list yourself from what the user already said. Do NOT stop to ask "is this the right scope?" when the conversation already makes it clear.

**When to ask questions:** If and only if the scope has genuine ambiguity (multiple valid interpretations, missing critical info), batch ALL questions into a single `AskUserQuestion` call. Ask everything you need in one shot. Do not ask "should I proceed?" or "is this correct?" after presenting a plan: the user invoked this skill to get autonomous execution, not a confirmation loop.

**When to skip questions entirely:** If the user already specified the scope (e.g., "implement KUT-268 phases B-G", "fix this bug", "add feature X"), go straight to Step 2. The conversation IS the scope confirmation.

After resolving scope, announce once:

> OK, implementing [scope summary]. Using TDD.

Then proceed immediately to Step 2.

## Step 2: Plan Tasks

Create `TaskCreate` todos for every work item in scope, in execution order. Each todo needs clear success criteria. Set up dependencies with `TaskUpdate`. This is the full punch list: don't start coding until it's complete.

## Step 3: Detect Verification Mode

Auto-detect from the files being changed. The user can override explicitly.

| Signal | Mode |
|--------|------|
| UI components, screens, CSS/styles | **Visual UI** |
| SKILL.md, agents/, evals/, prompts | **Skill EDD** |
| Everything else (API, CLI, library, backend) | **Backend/CLI** |

## Step 4: Execute (one-shot, no pausing)

Work through each todo sequentially. Mark `in_progress` when starting, `completed` when done. Do NOT stop between items unless you hit a fail-safe. Do NOT re-confirm scope mid-execution.

---

## Verification Modes

### Backend/CLI (Mode 3)

Red-green-refactor with the project's native test runner.

1. Write a failing test
2. Write minimal code to pass it
3. Run tests
4. Refactor
5. Run tests again
6. Next unit of work

Auto-detect runner: Go (`go test`), Node (`npm test` / `vitest`), Python (`pytest`), Rust (`cargo test`), Shell (`bats`). Prefer `Taskfile.yml` or `Makefile` test targets when available.

### Visual UI (Mode 1)

Screenshot-driven verification. No unit tests: the screenshot IS the assertion.

1. Write acceptance criteria (what should the screen look like?)
2. Implement
3. Take screenshot (Playwright MCP for web, WDA for iOS, ADB for Android)
4. Evaluate against criteria
5. Fix and re-screenshot until pass
6. Refactor, re-verify

### Skill EDD (Mode 2)

Eval-driven development using `evals/evals.json`.

1. **RED**: Write eval scenarios (direct, indirect, negative control, edge case)
2. **GREEN**: Write minimal SKILL.md to pass
3. **VERIFY**: A/B against baseline arm (old skill or no skill)
4. **REFACTOR**: Improve without breaking evals
5. **EXPAND**: Add harder evals, repeat

Run evals with fresh executor subagents (no contamination). Grader subagents (haiku) score per assertion. Deterministic checks (file exists, regex) go in scripts, not graders.

---

## Rules

1. **Autonomous means autonomous**: once you start executing, do not pause for scope re-confirmation or "is this right?" checks. The user invoked this skill to get uninterrupted execution. Only stop for fail-safes.
2. **Make judgment calls**: pick the simpler option on ambiguity. Only ask the user for irreversible/architectural decisions (new dependency, schema change, public API shape).
3. **Fail-safe**: if verification fails 3 times on the same issue, stop and report what you tried.
4. **Stay in scope**: no speculative refactoring, no unrelated cleanup.
5. **30-minute rule**: if stuck on one item for 30+ minutes with no progress, pause and report: current task, what needs to work, evidence it doesn't.
6. **Don't stop early**: keep going until every scoped item is complete or you hit a fail-safe.
