---
name: git-group-commit-message
description: Group uncommitted changes by feature, write groups.json with files and commit messages, and generate a Taskfile that iterates and commits each group.
disable-model-invocation: true
---

# Git Group Commit Message

Analyze uncommitted changes, group them by feature, and emit runnable commit artifacts under `.scratch/commit/`:

- `GROUPS.md` — the numbered group plan (human-readable)
- `groups.json` — machine-readable array of `{ files, message }` objects
- `Taskfile.yml` — a `commit:group` task that reads `groups.json` and commits each group in sequence

This skill never commits. The user reviews `GROUPS.md` and `groups.json`, then runs:

```bash
task -t .scratch/commit/Taskfile.yml commit:group
```

## Context (auto-injected on supported platforms)

!git diff HEAD
!git status
!git log --oneline -10

## Steps

1. **Gather state** (review auto-injected context above, or run manually if not available):
   - `git status` — all modified/untracked files
   - `git diff HEAD` — full uncommitted diff (staged + unstaged)
   - `git log --oneline -20` — recent commits to identify already-committed work

2. **Check for remaining work**: If there are no uncommitted changes (no modified, no untracked files besides `.scratch/commit/` and `CONTINUE.md`), print "All groups committed." and stop.

3. **Read or create `.scratch/commit/GROUPS.md`**:
   - If it exists, read it and remove any groups whose files are ALL already committed (cross-check against `git status` — if every file in a group is clean, that group is done). Renumber the remaining groups from 1.
   - If it doesn't exist, or all groups in it are done, create it fresh from the current uncommitted changes.

4. **Identify feature groups** (only when creating fresh): Read the diff and cluster changes into groups a user would recognize as separate features. Each group should be independently committable. Use these signals:
   - Files in the same package/directory working toward the same goal
   - A new capability end-to-end (config + implementation + tests + CLI wiring)
   - Infrastructure/nix/build changes that support a specific feature vs. standalone fixes
   - Cross-check against `git log` — if a group's files were already partially committed, note what remains

5. **Write `.scratch/commit/GROUPS.md`** with the remaining (uncommitted) groups, numbered:

   ```markdown
   # 1. <Short Feature Name>

   ## Description
   <1-2 sentence summary of what this group does and why>

   ## Files
   - `path/to/file1.go`
   - `path/to/file2.go`
   - `path/to/file3_test.go`
   ```

   Order groups by dependency — foundational changes first, CLI integration last.

   **When a file is contested between two features, prefer including it over excluding it.**
   Pull in whatever the group needs to compile and pass its own tests, even if that means a
   bigger commit than the "pure" feature split. But bound it: if including a file drags in a
   transitive chain that swallows an unrelated feature wholesale, stop — split the *feature*
   across commits instead. A feature spanning two commits is fine; one commit swallowing the
   whole branch is not. Note in `.scratch/commit/GROUPS.md` which part was deferred and why.

6. **Verify and generate a message per group**: Run `git reset HEAD -- .` to clear staging, then for each group in order:

   - `git add` the group's files **cumulatively** (no reset between groups) — the index now
     matches exactly what that group's commit will contain on top of the previous ones.
   - **Verify the staged tree compiles standalone** — the working tree hides missing
     dependencies, because uncommitted files from later groups are still on disk. Extract the
     index and build it in isolation:

     ```bash
     S=$(mktemp -d); git archive "$(git write-tree)" | tar -x -C "$S"
     cp -r <any gitignored-but-required dirs> "$S/"   # e.g. generated docs/
     (cd "$S" && go build ./... && go test ./<changed pkgs>/...)
     ```

     If it fails, move the offending files into the group that defines their dependencies (or
     pull the dependency in, per the rule above), rewrite `GROUPS.md`, and re-check. Compare
     any failure against the same build of plain `HEAD` before treating it as caused by this
     group — some failures are pre-existing.
   - **Invoke the `git-commit-message` skill** (via the Skill tool) to generate this group's
     commit message. The sub-skill owns format, conventional commit rules, ticket extraction,
     and quality checks — do NOT write commit messages yourself. Before invoking, stage only
     this group's files so the sub-skill's `git diff HEAD` sees the right scope. After it
     writes `.scratch/COMMIT.md`, read the result for inclusion in `groups.json`.
     Fetch Linear / Jira tickets once on the first group and reuse for all subsequent groups.

   After the last group, run `git reset HEAD -- .` so the working tree starts clean.

7. **Write `.scratch/commit/groups.json`** — a JSON array, one object per group in order:

   ```json
   [
     {
       "id": 1,
       "name": "JWT auth middleware",
       "files": ["pkg/auth/middleware.go", "pkg/auth/config.go"],
       "message": "feat(auth): add JWT validation middleware\n\n- feat(auth): add JWT validation — rejects unsigned tokens at the edge\n- test(auth): add middleware unit tests"
     },
     {
       "id": 2,
       "name": "Dashboard redesign",
       "files": ["web/dashboard.tsx", "web/styles.css"],
       "message": "feat(ui): redesign dashboard layout\n\n- feat(ui): new grid layout — reduces scroll depth by 40%"
     }
   ]
   ```

   - `files`: repo-relative paths (no `:/` prefix — the Taskfile adds it)
   - `message`: the full commit message from the `git-commit-message` skill, with `\n` for newlines

8. **Write `.scratch/commit/Taskfile.yml`** — a static Taskfile that reads `groups.json` and iterates:

   ```yaml
   version: '3'

   tasks:
     commit:group:
       desc: Read groups.json and commit each group in sequence
       cmds:
         - |
           set -euo pipefail
           GROUPS="$(cat ./groups.json)"
           COUNT=$(echo "$GROUPS" | jq length)
           for i in $(seq 0 $((COUNT - 1))); do
             GROUP=$(echo "$GROUPS" | jq -r ".[$i]")
             NAME=$(echo "$GROUP" | jq -r '.name')
             echo "=== Group $((i+1))/$COUNT: $NAME ==="
             # reset index so only this group's files are staged
             git reset HEAD -- . 2>/dev/null || true
             # stage files
             FILES=$(echo "$GROUP" | jq -r '.files[]')
             while IFS= read -r f; do
               git add -- ":/$f"
             done <<< "$FILES"
             # commit with message from json
             echo "$GROUP" | jq -r '.message' | git commit -F -
             echo
           done
           echo "All $COUNT groups committed."
   ```

   The Taskfile is static (never changes between runs). All group data lives in `groups.json`,
   so the user edits messages there (or in `GROUPS.md` and re-invokes the skill).

9. **Print summary**:
   - Numbered groups with file counts and each message's header line
   - "Review/edit groups.json, then run `task -t .scratch/commit/Taskfile.yml commit:group`."

## Notes
- If all changes are already committed, say so and skip.
- If a file belongs to multiple features, assign it to the group where it has the most impact and note the overlap.
- Untracked files (new files) should be included in the analysis — check them with `git diff --no-index /dev/null <file>` or read them directly.
- `CONTINUE.md` and everything under `.scratch/commit/` are excluded from feature groups.
- This skill only writes artifacts — it never commits. The generated Taskfile does the committing.
- If `task commit:group` fails midway (e.g. a hook rejects a commit) or is interrupted, fix the cause and re-invoke this skill: it prunes committed groups and regenerates the artifacts for what remains.

## Examples

**12 changed files across auth and UI:** Skill creates 2 groups in `GROUPS.md` and `groups.json`: (1) "JWT auth middleware" (4 files), (2) "Dashboard redesign" (8 files). Outputs: "2 groups written to .scratch/commit/. Review groups.json, then run `task -t .scratch/commit/Taskfile.yml commit:group`."

**Re-invocation after a partial run:** Group 1 was committed, then a pre-commit hook rejected group 2. Skill detects group 1's files are clean, drops it, renumbers "Dashboard redesign" to group 1, and regenerates `groups.json` and `GROUPS.md` with only that group.
