---
name: ai-rebase
description: Generate improved commit messages for a git commit range using parallel subagents, without creating commits.
argument-hint: <git range, e.g. main..HEAD>
disable-model-invocation: true
---

Generate improved commit messages for a git range. Do NOT create actual commits.

Input range: $ARGUMENTS

## Step 1: Setup

Run: `mkdir -p .scratch`
Run: `git log --reverse --oneline $ARGUMENTS`

Count the commits. Process them in batches using parallel Agent subagents (one batch per agent, ~15 commits each). Each agent gets a slice of hashes and writes `.scratch/COMMIT-<hash>.md` files independently.

## Step 2: Spawn parallel agents

Split the commit list into batches of 15. For each batch, launch an Agent with `subagent_type: "general-purpose"` and `model: "sonnet"`. Give each agent:
- The list of hashes it's responsible for
- The full instructions below (copy the "Per-commit instructions" section verbatim into the agent prompt)

Run all agents in parallel. Wait for all to complete.

## Step 3: Report

After all agents finish, count the `.scratch/COMMIT-*.md` files and print:
```
Done: <count> commits → .scratch/
```

---

## Per-commit instructions (give this to each agent verbatim)

For each commit hash in your batch, do steps A–D:

**A) Read the diff.** Run: `git show <hash> --format="" | head -300`

For merge commits (check: `git rev-list --parents -n1 <hash>` has 3+ words): run `git show <hash> --stat -m --first-parent` instead.

Read the diff carefully. Look at function names, struct fields, route handlers, SQL, config keys. These tell you what actually changed.

**B) Analyze.** Determine:
- Scope: which subsystem changed. Map file paths to scopes:
  - `internal/agent/` or `cmd/agent/` → `agent`
  - `internal/api/` or `handler/` or `routes/` → `api`
  - `internal/cdc/` or `binlog/` → `cdc`
  - `internal/crm/` or `leads/` or `lifecycle/` → `crm`
  - `internal/ingestion/` or `leadsync/` → `ingestion`
  - `internal/email/` or `gmail/` → `email`
  - `internal/sms/` or `dialpad/` → `sms`
  - `temporal/` or `workflow/` → `worker`
  - `db/` or `models/` or `migrations/` or `schema/` → `db`
  - `helm/` or `charts/` → `helm`
  - `Dockerfile` or `docker-compose` → `docker`
  - `Makefile` or `Taskfile` or `.github/` → `infra`
  - `tui/` or `bubbletea/` → `tui`
  - `config/` or `settings/` or `env` → `config`
  - `auth/` or `rbac/` → `auth`
  - `*_test.go` → `tests`
- Type: `feat|fix|refactor|test|docs|chore`
- Impact: what a user, operator, or API consumer would notice

**C) Write `.scratch/COMMIT-<7-char-hash>.md`** — use the FIRST 7 characters of the hash in the filename. Content must be exactly:

```
---
hash: <full-hash>
original: "<original one-line message>"
---
[apps/pdk] <New summary — what changed for the user/system>
- type(scope): what changed — consequence for users/operators
```

⚠️ **CRITICAL:** Filename uses 7-char hash (e.g., `COMMIT-0d6ad22.md`). File content has full hash in frontmatter. NO extra blank lines. NO markdown headings inside the file. NO extended metadata sections.

**D) Print status.** Use short hash (7 chars) in output:
- Normal: `✓ <7-char-hash> [apps/pdk] <summary>`
- Merge: `⊕ <7-char-hash> [apps/pdk] merge: <what was merged>`
- No-op: `⊘ <7-char-hash> skip`

---

## Quality rules

1. **Summary must be NEW** — never repeat the original message. Rewrite it to answer "what changed for the user/system?"
   - Bad: "LLM based skill routing"
   - Good: "Agent routes inbound requests to skills via LLM classification"

2. **Impact = consequence, not mechanism.**
   - Bad: "detect stale Docker images via DockerfileChanged" / "9 files modified"
   - Good: "stale containers are caught before deployment"

3. **Lead with impact, not implementation.** Before the em-dash: name the change. After: why anyone cares.
   - Bad: "add handleLeadAssignment function — handles lead assignment"
   - Good: "add automatic lead assignment — new leads route to available reps without manual intervention"

4. **Scope must match the subsystem** — not `tests` for everything. Use the file path mapping above.

5. **Don't mix unrelated changes in the header.** If a commit has a feat + a chore, only the feat goes in the header.

6. **NO blank lines anywhere in the file** except a trailing newline. No blank line between `---` and `[apps/pdk]`. No blank line between summary and first bullet. No extra markdown sections, no headers inside file.

7. **Max 5 bullets** unless genuinely large. `chore`/`test` bullets stay short.

8. **Filename is CRITICAL:** `COMMIT-<7-char-hash>.md` — use first 7 chars only. Do NOT write `COMMIT-<full-40-char-hash>.md`.

## Example correct output

```
---
hash: 77b642bfe64c02b076e0bd028b00411eaf41259b
original: "Add Gmail gateway with send, fetch, and auth via domain-wide delegation"
---
[apps/pdk] CRM can send and receive email via Gmail domain-wide delegation
- feat(email): add Gmail gateway with OAuth2 service account auth — CRM agents can send/receive email without per-user OAuth consent
- feat(email): implement fetch for inbox threads — conversation view now shows email history alongside SMS
- chore(config): add Google service account credentials to secrets config — no user impact
```

## Example WRONG output

```
---
hash: 77b642bfe64c02b076e0bd028b00411eaf41259b
original: "Add Gmail gateway with send, fetch, and auth via domain-wide delegation"
---

[apps/pdk] Add Gmail gateway with send, fetch, and auth via domain-wide delegation

- feat(tests): Add Gmail gateway — 5 files modified
```

Wrong because: blank line after `---`, blank line between summary and bullets, repeats original, wrong scope, useless impact.
