# Commit Message Format

Every generated message uses this exact format:

```
[ABC-xxx, ABC-yyy] <One-line summary of what changed that matters to a user, API consumer, or integration>

- feat(component): <what changed> — <user/api/integration impact>
- fix(component): <what changed> — <user/api/integration impact>
- refactor(component): <what changed> — no user-facing impact
- test(component): <what changed>
- chore(infra): <what changed>
```

## Format rules

- **First line** (header): ticket IDs in brackets, then a plain-English summary of the most impactful changes — written for a person reading the git log, not for a developer. Focus on API/behaviour/user-visible changes. Omit internal refactors from the header.
- **Second line**: blank
- **Bullet list**: every change is a `-` list item in conventional commit format (`feat/fix/refactor/test/docs/chore(scope): description`). No standalone subject line — the primary commit type goes first in the list. Each bullet ends with an em-dash and the impact (or `no user-facing impact` for internal-only changes).
- **Every claim must be backed by the diff.** Never invent an impact to fill the em-dash slot. If the diff cannot establish the consequence (dependency/lockfile bumps, vendored updates), name what changed instead — e.g. `chore(deps): bump claude-code.nix, home-manager, nixpkgs pins — picks up upstream changes` — and never assert `no functional impact` for them. Keep separate mechanisms separate: credit each effect to the change that actually causes it.
- Scope should reflect the actual component: `worker`, `api`, `db`, `schemas`, `infra`, `tests`, `migrations`, `lib`
- **Every bullet MUST have a scope** — `test:` alone is invalid, use `test(runner):` or `test(cfg):`. If tests span multiple areas, either split into separate bullets per area or use `test(all):`. Never omit the parenthesized scope.
- Do NOT include speculative or future changes — only what is in the diff
- **Bullets describe purpose, not file location.** `feat(auth): Add JWT validation` ✅ — not `Update auth.ts` ❌.
- **Cap at ~7 bullets.** If you have 10+, group by purpose more aggressively (e.g., one bullet for "Add RBAC (middleware + admin panel + API + tests)", not four).
- **Header names the highest-tier change** when multiple types are present. Priority: breaking > user-facing (feat/fix/perf) > internal (refactor/chore/test/docs). A commit with a breaking auth change and a UI refactor gets a header about the auth change.
- **Breaking changes:** use `feat(api)!:` (! suffix) OR `feat(api): BREAKING: ...` (prefix) — not both.
- If no Linear / Jira tickets are found, omit the `[ABC-xxx]` prefix and start directly with the plain-English header (never a `type(scope):` prefix — types live on the bullets).
- Ticket IDs in the header are plain text only: `[ABC-166, ABC-167]` — no markdown links, no parent ticket references.
- Keep bullet descriptions concise (one line each); use the Linear / Jira ticket title to inform the language but don't copy-paste it verbatim.

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

## Self-assessment checklist

Before finalizing each message, verify:

- [ ] Message follows conventional commit format (type(scope): description)
- [ ] Type matches the nature of changes (feat/fix/chore/refactor/docs)
- [ ] Header is plain English stating the outcome — imperative ("Add email validation to signup") or descriptive ("Signup now rejects malformed emails"); no `type(scope):` prefix
- [ ] Every impact clause is supported by the diff (no invented or unprovable impact)
- [ ] Every bullet has a parenthesized scope and an impact clause

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
