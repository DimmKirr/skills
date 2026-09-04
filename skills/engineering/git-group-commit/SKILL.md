---
name: git-group-commit
description: Group uncommitted changes into feature commits with conventional messages, and emit runnable commit artifacts. Use when the user asks to commit changes, write or improve a commit message, split work into multiple commits, or another skill needs commit messages for uncommitted changes. A single change is handled as one group. Do NOT use for PR descriptions (git-pr-message owns those).
model: sonnet
---

# Git Group Commit

Analyze uncommitted changes, group them by feature, generate a conventional commit message per group, and emit runnable commit artifacts inside the git dir (`$(git rev-parse --git-dir)/`, normally `.git/`) so they never pollute the working tree and can never be committed by accident:

- `commits.json` — the single source of truth: `{ groups: [...], excluded: [...] }` holding the full plan (files, descriptions, messages, exclusions)
- `group-commit.sh` — a static runner that reads `commits.json` and commits each group in sequence, wired to a repo-local git alias so it runs as `git group-commit`

A single logical change is not a special case — it produces one group and the same flow.

This skill never commits. The user reviews `commits.json` (the summary printed at the end is the human-readable view of it), then runs:

```bash
git group-commit
```

## Context (auto-injected on supported platforms)

!git diff HEAD
!git status
!git log --oneline -10

## Execution modes

**Workflow mode (preferred, Claude Code):** if the Workflow tool is available, do not execute steps 3–9 inline. Instead invoke, using this skill's base directory (announced when the skill loaded) as the script path:

```
Workflow({ scriptPath: "<skill base dir>/scripts/workflow.js",
           args: { stateKey: "<output of: git status --porcelain | git hash-object --stdin>" } })
```

Always pass `args.stateKey` (one cheap shell command) — it keys the plan agent's cache to the working-tree state, so resuming after commits or edits re-plans instead of replaying a stale cached plan. Optionally add `skillDir: "<skill base dir>"`; without it the script defaults to `~/.claude/skills/git-group-commit` and agents fall back to locating the folder.

The script owns model selection — planning and per-group message generation run on Sonnet (messages fan out in parallel, one agent per group), artifact assembly runs on Haiku — so the session model never burns tokens on this. When it completes, relay its returned summary (groups, headers, exclusions, next command) per step 10.

**Inline mode (fallback, Codex or Workflow unavailable):** execute all steps below yourself, with one substitution — in step 7, do NOT write messages with the session model. For each group run:

```bash
sh <skill dir>/scripts/codex-msg.sh <skill dir> <tmpfile> <group files...>
```

and read the message from `<tmpfile>`. The script delegates to `codex exec` with a pinned cheap model (`GROUP_COMMIT_MSG_MODEL`, default `gpt-5.1-codex-mini`), so message generation costs mini-model tokens even when the session runs a frontier model. Planning (steps 3–5) stays on the session model — grouping is the judgment-heavy part. If the `codex` CLI is unavailable, fall back to writing messages inline.

## Steps

1. **Gather state** (review auto-injected context above, or run manually if not available):
   - `git status` — all modified/untracked files
   - `git diff HEAD` — full uncommitted diff (staged + unstaged)
   - `git log --oneline -20` — recent commits to identify already-committed work
   - `git branch --show-current` — for ticket ID extraction (step 6)

2. **Check for remaining work**: If there are no uncommitted changes (no modified, no untracked files besides `CONTINUE.md`), print "All groups committed." and stop. Set `GIT_DIR=$(git rev-parse --git-dir)` — all artifacts below live there.

3. **Read or create `$GIT_DIR/commits.json`**:
   - If it exists, read it and remove any groups whose files are ALL already committed (cross-check against `git status` — if every file in a group is clean, that group is done). No renumbering needed — array position is the only ordering.
   - If it doesn't exist, or all groups in it are done, plan fresh from the current uncommitted changes.

4. **Identify feature groups** (only when creating fresh): Read the diff and cluster changes into groups a user would recognize as separate features. Each group should be independently committable. One group total is a normal outcome. Use these signals:
   - Files in the same package/directory working toward the same goal
   - A new capability end-to-end (config + implementation + tests + CLI wiring)
   - Infrastructure/nix/build changes that support a specific feature vs. standalone fixes
   - Cross-check against `git log` — if a group's files were already partially committed, note what remains

   Order groups by dependency — foundational changes first, CLI integration last. Give each
   group a short name and a 1-2 sentence description (both land in `commits.json`, step 8).

   **When a file is contested between two features, prefer including it over excluding it.**
   Pull in whatever the group needs to compile and pass its own tests, even if that means a
   bigger commit than the "pure" feature split. But bound it: if including a file drags in a
   transitive chain that swallows an unrelated feature wholesale, stop — split the *feature*
   across commits instead. A feature spanning two commits is fine; one commit swallowing the
   whole branch is not. Note in the group's `notes` field which part was deferred and why.

5. **Verify each group compiles standalone** (skip when there is only one group — nothing is being split): Run `git reset HEAD -- .` to clear staging, then for each group in order:

   - `git add` the group's files **cumulatively** (no reset between groups) — the index now
     matches exactly what that group's commit will contain on top of the previous ones.
   - Extract the index and build it in isolation — the working tree hides missing
     dependencies, because uncommitted files from later groups are still on disk:

     ```bash
     S=$(mktemp -d); git archive "$(git write-tree)" | tar -x -C "$S"
     cp -r <any gitignored-but-required dirs> "$S/"   # e.g. generated docs/
     (cd "$S" && go build ./... && go test ./<changed pkgs>/...)
     ```

     If it fails, move the offending files into the group that defines their dependencies (or
     pull the dependency in, per the rule above), update the plan, and re-check. Compare
     any failure against the same build of plain `HEAD` before treating it as caused by this
     group — some failures are pre-existing.

   After the last group, run `git reset HEAD -- .` so the working tree starts clean.

6. **Extract ticket IDs and fetch tickets once** (reused for every group's message):
   - From the branch name (e.g. `username/ABC-166-...` → `ABC-166`), existing commits on this branch, and `[ABC-xxx]` patterns in the diff
   - Fetch each from Linear / Jira MCP in parallel: `get_issue` with `includeRelations: true`; capture `identifier`, `title`, short `description`, `state.name`, and parent identifier/title if present
   - If no tickets are found, messages omit the `[ABC-xxx]` header

7. **Generate a message per group** — scoped strictly to that group's files:
   - Diff only the group: `git diff HEAD -- <group files>` (plus `git diff --no-index /dev/null <file>` for untracked files). Never generate a message from the full-tree diff.
   - Follow [references/format.md](references/format.md) exactly — it owns the message format, conventional commit rules, the initial-commit special case, and the user-impact quality check.
   - Only tag a group's header with ticket IDs whose work that group actually contains.

8. **Write `$GIT_DIR/commits.json`** — the single source of truth for the whole plan:

   ```json
   {
     "groups": [
       {
         "name": "JWT auth middleware",
         "description": "Adds JWT validation at the edge so unsigned tokens are rejected before hitting handlers.",
         "notes": "config refactor deferred to group 2 — would have dragged in the whole settings package",
         "files": ["pkg/auth/middleware.go", "pkg/auth/config.go"],
         "message": "[AUTH-42] Add JWT validation middleware\n\n- feat(auth): add JWT validation — rejects unsigned tokens at the edge\n- test(auth): add middleware unit tests"
       }
     ],
     "excluded": [
       { "path": ".env.local", "reason": "local secrets — never commit" }
     ]
   }
   ```

   - Groups have no `id` field — array order IS commit order, and display numbering (1-based) derives from position, so reordering or deleting entries can never leave stale ids
   - `groups[].files`: repo-relative paths (no `:/` prefix — the runner adds it)
   - `groups[].message`: the full commit message with `\n` for newlines
   - `groups[].diffHash`: staleness fingerprint — compute with `sh <skill dir>/scripts/group-commit.sh --hash <group files...>` and always set it. The runner recomputes it before committing and refuses the group (exit 3, kept in the plan) if the content changed since planning — this is what makes a stale plan unable to happy-commit
   - `groups[].notes`: optional — deferred parts, contested files, caveats
   - `excluded`: uncommitted paths deliberately left out of every group, with the reason (personal files, local environment, generated state). Persisting them keeps re-invocations from re-proposing them.

9. **Install the `git group-commit` command** — copy the runner shipped with this skill and wire the repo-local alias. Skip if already present and identical:

   ```bash
   cp <skill dir>/scripts/group-commit.sh "$GIT_DIR/group-commit.sh"
   chmod +x "$GIT_DIR/group-commit.sh"
   git config alias.group-commit '!sh "$(git rev-parse --git-dir)/group-commit.sh"'
   ```

   The runner ([scripts/group-commit.sh](scripts/group-commit.sh)) is static and copied
   verbatim — never rewrite or inline it. It supports `git group-commit` (commit each group
   in sequence), `--dry-run`/`-n`/`--review` (print the full plan without committing),
   `--skip-groups=1,3` (commit only the others; skipped groups stay in `commits.json`),
   `--force` (override the duplicate and staleness guards — a group whose subject line
   already exists in the last 100 commits, or whose content no longer matches its
   `diffHash`, is otherwise blocked with exit 3 and kept in the plan),
   `--hash <files...>` (print the staleness fingerprint planners store as `diffHash`),
   `--no-color` (ANSI colors are otherwise auto: TTY-only, `NO_COLOR` honored), and
   `--help`. Committed (or already-clean) groups are popped from `commits.json` on exit, so
   re-running is idempotent and only skipped/remaining groups survive; a fully-committed plan
   reports itself empty. All plan data lives in `commits.json`, so the user edits messages,
   files, or group order there directly (or re-invokes the skill). The alias is repo-local
   (`.git/config`), so `git group-commit` works from any subdirectory of this repo and
   nowhere else.

10. **Print summary**:
    - Numbered groups with description, file count, and each message's header line
    - Excluded paths with reasons
    - For a single group, also print the full message inline so it can be reviewed at a glance
    - "Review with `git group-commit --dry-run` (a.k.a. `--review`; edit `$GIT_DIR/commits.json` to adjust), then run `git group-commit`."

## Notes

- DO NOT create actual commits. NEVER add/insert `Co-Authored-By: Claude` (or any other AI attribution trailer) anywhere — not in generated messages, not in `commits.json`, not in commits.
- If all changes are already committed, say so and skip.
- If a file belongs to multiple features, assign it to the group where it has the most impact and note the overlap.
- Untracked files (new files) are part of the analysis — read them directly or diff with `git diff --no-index /dev/null <file>`.
- `CONTINUE.md` is excluded from feature groups. Skill artifacts live inside the git dir, so they can never appear in `git status` or a commit.
- If `git group-commit` fails midway (e.g. a hook rejects a commit) or is interrupted, fix the cause and re-invoke this skill: it prunes committed groups and regenerates the artifacts for what remains.

## Examples

**12 changed files across auth and UI:** Skill creates 2 groups: (1) "JWT auth middleware" (4 files), (2) "Dashboard redesign" (8 files). Outputs: "2 groups written to .git/. Review with `git group-commit --dry-run`, then run `git group-commit`."

**Single bugfix (2 files):** Skill creates 1 group, skips the standalone-build check, writes `commits.json` with one entry, and prints the full commit message inline alongside the run instruction.

**Re-invocation after a partial run:** Group 1 was committed, then a pre-commit hook rejected group 2. Skill detects group 1's files are clean, drops it, and regenerates `commits.json` with "Dashboard redesign" as the only remaining group.
