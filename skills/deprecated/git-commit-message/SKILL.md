---
name: git-commit-message
description: Generate a structured conventional commit message for current changes and save it to .scratch/COMMIT.md. Use when the user asks to write, generate, or improve a commit message, is about to commit and needs a message, or another skill needs a commit message for staged changes. Do NOT use for PR descriptions (git-pr-message owns those).
---

# Commit Message Generator
IMPORTANT!
DO NOT ANY MENTION OF Co-Authored-By: Claude
DO NOT CREATE ACTUAL COMMITS

Generate a structured commit message for the current changes and save it to `.scratch/COMMIT.md`.

## Context (auto-injected on supported platforms)

!git diff HEAD
!git log --oneline -5
!git branch --show-current

## Steps

1. **Gather git context** (review auto-injected context above, or run manually if not available):
   - `git branch --show-current` — extract ticket IDs from branch name (e.g. `ABC-166` → `ABC-166`)
   - `git status` — see what files are staged/modified
   - `git diff HEAD` — full diff of all uncommitted changes (staged + unstaged)
   - Determine the correct base branch:
     1. Try `git fetch origin main 2>/dev/null` then use `origin/main`
     2. If fetch fails (no SSH keys, no network), check if local main tracks remote: `git branch -vv | grep main` — if it says "behind N", **warn the user** that local main is stale and the diff may be inflated
     3. Fall back to local `main` only if fetch fails, with the warning in the output
   - `git diff <base>...HEAD` — commits already on this branch vs base

2. **Extract all ticket IDs** from:
   - The branch name (e.g. `username/ABC-166-...` → `ABC-166`)
   - Existing commits on this branch: `git log <base>...HEAD --oneline` (using the same base from step 1) — scan for `[ABC-xxx]` or `ABC-xxx` patterns
   - Any `[ABC-xxx]` patterns found in the diff itself

3. **Fetch each ticket from Linear / Jira MCP** (run in parallel for all discovered IDs):
   - Use `get_issue` with `includeRelations: true` for each ticket ID
   - Capture: `identifier`, `title`, `description` (first 2–3 sentences only), `state.name`, `parent.identifier` + `parent.title` if present
   - If a ticket has a parent, also fetch the parent with `get_issue` to get its title
   - Build a ticket map: `{ "ABC-166": { title: "...", parent: "ABC-100" }, ... }`

4. **Analyze the diff** to identify:
   - Which components changed (e.g. `worker`, `api`, `db`, `schemas`, `infra`, `tests`)
   - The nature of each change (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`)
   - User/API/integration impact: what a downstream consumer would notice

5. **Write `.scratch/COMMIT.md`** using this exact format:

```
[ABC-xxx, ABC-yyy] <One-line summary of what changed that matters to a user, API consumer, or integration>

- feat(component): <what changed> — <user/api/integration impact>
- fix(component): <what changed> — <user/api/integration impact>
- refactor(component): <what changed> — no user-facing impact
- test(component): <what changed>
- chore(infra): <what changed>
```

6. **Print the file contents** so the user can copy-paste as the git commit message.

## Format rules

- **First line** (header): ticket IDs in brackets, then a plain-English summary of the most impactful changes — written for a person reading the git log, not for a developer. Focus on API/behaviour/user-visible changes. Omit internal refactors from the header.
- **Second line**: blank
- **Bullet list**: every change is a `-` list item in conventional commit format (`feat/fix/refactor/test/docs/chore(scope): description`). No standalone subject line — the primary commit type goes first in the list. Each bullet ends with an em-dash and the impact (or `no user-facing impact` / `no impact`).
- Scope should reflect the actual component: `worker`, `api`, `db`, `schemas`, `infra`, `tests`, `migrations`, `lib`
- **Every bullet MUST have a scope** — `test:` alone is invalid, use `test(runner):` or `test(cfg):`. If tests span multiple areas, either split into separate bullets per area or use `test(all):`. Never omit the parenthesized scope.
- Do NOT include speculative or future changes — only what is in the diff
- **Bullets describe purpose, not file location.** `feat(auth): Add JWT validation` ✅ — not `Update auth.ts` ❌.
- **Cap at ~7 bullets.** If you have 10+, group by purpose more aggressively (e.g., one bullet for "Add RBAC (middleware + admin panel + API + tests)", not four).
- **Header names the highest-tier change** when multiple types are present. Priority: breaking > user-facing (feat/fix/perf) > internal (refactor/chore/test/docs). A commit with a breaking auth change and a UI refactor gets a header about the auth change.
- **Breaking changes:** use `feat(api)!:` (! suffix) OR `feat(api): BREAKING: ...` (prefix) — not both.

## Special case: initial commit

If the diff is ONLY additions (all files new, no modifications, no deletions), this is an initial commit. Use this format instead:

```
[TICKET or WIP] Initial commit: <project name/description>

- feat(scope): High-level capability provided
- feat(scope): High-level capability provided
- chore(scope): Infrastructure or tooling provided
```

Focus on capabilities provided, not file listings. 5-7 bullets max. Prefer `feat` over `refactor`/`fix` (nothing exists to refactor or fix yet).

## User-impact quality check

After drafting, review every line against these rules:

1. **Header must answer "what changed for the user?"** — not "what code changed". Bad: "Fix stale image detection". Good: "cell no longer silently runs outdated containers after a failed build".
2. **Each bullet's impact clause (after the em-dash) must describe the consequence, not the mechanism.** Bad: "detect stale Docker images via DockerfileChanged and trigger rebuild". Good: "cell no longer silently uses a stale container after a failed docker build".
3. **Lead with the impact, not the implementation.** The part before the em-dash names the change; the part after explains why anyone should care. If the impact clause restates the change in different words, rewrite it.
4. **`chore` and `test` bullets get short impact clauses** — these are internal, so a brief note is fine. Don't inflate them.
5. **Don't mix unrelated changes in the header.** If the commit has a user-facing fix + an unrelated chore, only the fix goes in the header. The chore lives in the bullet list.

## Notes

- If no Linear / Jira tickets are found, omit the `[ABC-xxx]` header and start directly with the conventional commit subject
- If there are no staged changes but there are unstaged changes, note that in the output and generate the message for the full set of uncommitted changes
- Keep bullet descriptions concise (one line each); use the Linear / Jira ticket title to inform the language but don't copy-paste it verbatim
- Ticket IDs in the header are plain text only: `[ABC-166, ABC-167]` — no markdown links, no parent ticket references

## Self-Assessment Checklist

Before presenting output to the user, verify:

- [ ] Message follows conventional commit format (type(scope): description)
- [ ] Type matches the nature of changes (feat/fix/chore/refactor/docs)
- [ ] Description is imperative mood, under 72 characters
- [ ] Saved to .scratch/COMMIT.md

## Examples

**Feature addition** (branch: `dimmkirr/AUTH-42-email-validation`):
```
[AUTH-42] Add email format validation to registration flow

- feat(auth): add RFC 5322 email validation on signup — rejects malformed emails before hitting the API
- test(auth): add validation edge cases (unicode, plus-addressing, missing TLD)
```

**Bug fix** (branch: `fix/stale-cache`):
```
Fix stale cache serving outdated dashboard data after deploy

- fix(api): invalidate CDN cache on deploy webhook — dashboard no longer shows yesterday's metrics after a release
- chore(infra): add cache-bust header to static asset responses — no user-facing impact
```
