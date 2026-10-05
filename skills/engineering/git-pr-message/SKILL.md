---
name: git-pr-message
description: Generate a pull request description from committed groups and save it to .scratch/PR.md.
disable-model-invocation: true
---

# PR Message Generator

Generate a pull request description from committed groups and save it to `.scratch/PR.md`.

## Context (auto-injected on supported platforms)

!git log --oneline main..HEAD
!git diff main...HEAD --stat
!git branch --show-current

## Steps

1. **Gather context** (review auto-injected context above, or run manually if not available):
   - `git branch --show-current` — extract ticket IDs from branch name
   - `git log --oneline -20` — recent commits on this branch
   - Determine the correct base branch:
     1. Try `git fetch origin main 2>/dev/null` then use `origin/main`
     2. If fetch fails, fall back to local `main` with a warning
   - `git log <base>...HEAD --oneline` — all commits on this branch vs base
   - Read `.scratch/COMMIT-GROUPS.md` if it exists — use it to understand the grouping intent
   - Find the repo's PR template (first match wins): `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `PULL_REQUEST_TEMPLATE.md`, `docs/pull_request_template.md` (any case) — read it if found

2. **Extract all ticket IDs** from:
   - The branch name (e.g. `username/DEVOPS-106-...` → `DEVOPS-106`)
   - Commit messages on this branch: scan for `[ABC-xxx]` or `ABC-xxx` patterns
   - Collect unique IDs, preserving order of first appearance

3. **Fetch each ticket from Linear / Jira MCP** (run in parallel for all discovered IDs):
   - Use `get_issue` with `includeRelations: true` for each ticket ID
   - Capture: `identifier`, `title`, `description` (first 2–3 sentences only), `parent.identifier` + `parent.title` if present
   - If a ticket has a parent, also fetch the parent to get its title

4. **Analyze all commits** on this branch:
   - Read each commit message (`git log <base>...HEAD --format='%H %s'`)
   - For each commit, extract the conventional commit bullets from the full message (`git log <base>...HEAD --format='%B---'`)
   - Deduplicate and merge bullets that describe the same change across commits
   - Group by type: features first, then fixes, then tests, then chores/docs

5. **Verify against the actual diff (CRITICAL — commit messages lie by omission)**: commit
   messages are the starting point, never the source of truth. Feature code gets absorbed
   into unrelated commits (rebases, squashes, commit-group reshuffles), so a user-facing
   change can exist in the diff with no commit bullet mentioning it. Before writing the
   file, sweep the real diff for user-facing surface and cross-check every hit against
   your draft:
   - `git diff <base>...HEAD -- <CLI/flag/config files>` — read the diffs of files that
     define user-facing surface (flag registration, config structs, env var reads,
     generated docs/options). `--stat` alone is not enough.
   - Grep the full diff's added lines for new surface: flags (`--[a-z-]+`), env vars
     (`[A-Z][A-Z0-9_]{3,}`), config/TOML keys (`toml:"..."`, YAML/JSON tags), new
     subcommands, and changed flag/option defaults.
   - Every hit must appear in the description as a feat/fix bullet — not merely inside a
     test bullet ("add coverage for X" does not surface feature X).
   - Watch for **behavior flips**: a default changing (opt-out → opt-in, on → off) or a
     flag becoming a no-op won't show as "removed or renamed" but IS a breaking change.
     Compare old vs new default values and flag handling in the diff.
   - A test-only commit whose message says it covers "already shipped" behavior is a red
     flag: verify where that behavior shipped. If it's inside this branch's diff, it needs
     its own feature bullet and its ticket ID belongs in the PR.

6. **Write `.scratch/PR.md`**. The file always starts with a `Title:` preamble, regardless of whether a repo template exists:

```
Title: <PR title>
---
<body — repo template reproduction, or the default format below>
```

   The `Title:` line is separate from the body even when the body's own template/default format also has a `#`-heading title (e.g. the default format's `# <PR title>` line) — never skip the preamble just because the body repeats or already contains a title-shaped heading. This preamble is what gets pasted into GitHub's PR title field; the body below the `---` is what gets pasted into the PR description box.

   **If a repo PR template was found, its structure wins for the body.** Reproduce the template exactly — same headings, same order, same boilerplate (warnings, checklists, links) — and fill its sections with the generated content: the summary goes into the "what does this PR do"-style section, the conventional-commit bullets into the "how did you implement it"-style section, the test plan into the testing section. Fill ticket placeholders in the template (e.g. `# [NPT-](…/NPT-)` → `# [NPT-3509](…/NPT-3509) <PR title>`). Keep optional sections present; leave them empty unless there is something relevant. Do not add headings the template doesn't have. The content rules below (scoped bullets, impact clauses, no SHAs, no Co-Authored-By) still apply inside each section.

   **Only if no template exists**, use this default format for the body:

```markdown
# <PR title: what users can now DO, e.g. "Add Wails 3 desktop shell alongside Electron">

## Summary

<2-3 sentences. Lead with what users can do now. Internal refactoring follows as context, never leads. Reference ticket IDs naturally.>

## Breaking changes

<Only if flags/commands/env vars were removed or renamed. Omit this section entirely if nothing breaks.>

## Changes

- feat(scope): description — impact
- feat(scope): description — impact
- fix(scope): description — impact
- refactor(scope): description
- chore(scope): description

## Test plan

- [ ] <concrete verification step>
- [ ] <concrete verification step>
```

7. **Print the file contents** so the user can copy-paste into the PR.

## Format rules

- **User-facing focus (CRITICAL)**: The title, body title, and summary must describe what users can now DO, not what code was moved/refactored/extracted. Internal reorganizations (repo splits, module extractions, build-path removals) belong in the Changes section, never in the title or summary lead. Ask: "If I'm a user who doesn't read source code, what changed for me?" That answer is the title. Refactors, extractions, and internal moves are means, not ends. A title like "Extract X into Y" fails this test; "Add feature Z" passes. If the branch is purely internal with no user-facing change, say what the user gains indirectly (e.g., "Faster builds" not "Split monorepo").
- **Breaking changes**: If any user-facing flags, env vars, config keys, or CLI commands were removed, renamed, turned into no-ops, or had their **default behavior flipped** (e.g. a feature going from on-by-default to opt-in), add a `## Breaking changes` section immediately after Summary listing each one, including how to restore the old behavior. Users scanning the PR need this before the full changelog.
- **`Title:` preamble**: one line, GitHub-PR idiomatic — imperative mood, no trailing period, ≤72 characters where possible (hard cap ~70; trim scope detail before dropping below this). Must name the single most important, most user-facing change first; if the branch bundles several changes, lead with the one a reviewer or changelog reader would care about most and summarize the rest only if it fits within the length budget — do not try to enumerate every change in the title, that's what the body's Changes section is for. Include ticket IDs in brackets if present (e.g. `[DEVOPS-108] Add Wails 3 desktop shell alongside Electron`). This is the line the author pastes into GitHub's PR title field, so it must stand alone without the body for context.
- **Body title** (`# ...`, only present in the default no-template format, or if the repo template itself has a `#` heading): one line summarizing user-affected features. Written for someone scanning a PR list — what capability landed, not what code changed. Include ticket IDs in brackets if present (e.g. `[DEVOPS-108] Add Wails 3 desktop shell alongside Electron`). May restate or closely match the `Title:` preamble — that duplication is expected and fine, they serve different UI slots (PR title field vs. PR description body).
- **Summary**: 2-3 sentences max. Name the ticket(s) naturally (e.g. "Implements DEVOPS-108"). Lead with what users can do now. Internal refactoring may follow as a second sentence ("Internally, X moved to Y"), never first.
- **Changes**: merged from all commit messages on the branch. Same `feat/fix/refactor/test/docs/chore(scope):` format as commit messages. Every bullet MUST have a parenthesized scope. Cap at ~10 bullets — group aggressively if there are more. Features and fixes first, refactors and chores last.
- **Deduplication**: if two commits touch the same area (e.g. one adds a feature, a later one fixes it), merge into one bullet describing the final state. The PR reader sees the end result, not the journey.
- **Test plan**: concrete steps a reviewer can follow. Prefer `task` / `pnpm` commands. Include build verification, test commands, and any manual checks. Pull from ticket's HOW-TO-TEST section if available.
- **No Co-Authored-By lines.**
- **No commit hashes or SHAs** in the output.
- Bullets describe purpose, not file location.
- Impact clauses describe consequences, not mechanisms.

## Notes

- If `.scratch/COMMIT-GROUPS.md` doesn't exist, derive grouping from commit messages directly.
- **Staleness check for `.scratch/COMMIT-GROUPS.md`**: it may describe a previous branch or already-merged work. Only use it if its files/features match the current `<base>...HEAD` diff; otherwise ignore it and say so.
- If no tickets are found, omit ticket references from the summary.
- If no conventional commit bullets exist in commit messages, synthesize them from the diff summary (`git diff <base>...HEAD --stat` + reading key changed files).

## Self-Assessment Checklist

Before presenting output to the user, verify:

- [ ] `Title:` preamble present, ≤72 chars, leads with the single most important user-facing change
- [ ] Title and summary pass the user-focus test: a non-developer reading only the title and summary knows what changed for them, not what code moved internally
- [ ] No refactor/extraction/internal-move language in the title or summary lead sentence
- [ ] Breaking changes section present if any flags/commands/env vars were removed, renamed, no-op'd, or had defaults flipped
- [ ] Diff sweep done (step 5): every new flag, env var, config key, and subcommand found in the diff has its own feat/fix bullet — none surfaced only via a test bullet
- [ ] Summary covers all commits on the branch
- [ ] Test plan includes verification steps
- [ ] No commits omitted from the description
- [ ] Saved to .scratch/PR.md

## Examples

**3 commits on branch** (`feature/DEVOPS-108-wails-desktop`), no repo PR template found:
```markdown
Title: [DEVOPS-108] Add Wails 3 desktop shell alongside Electron
---
# [DEVOPS-108] Add Wails 3 desktop shell alongside Electron

## Summary

Implements DEVOPS-108. Adds a Wails 3 desktop build target that shares the existing React frontend, giving users a native desktop app without Electron's memory overhead.

## Changes

- feat(desktop): add Wails 3 build configuration and Go backend — users can run the app as a native binary
- feat(build): add `task desktop:dev` and `task desktop:build` commands — developers can iterate on desktop builds locally
- test(desktop): add smoke tests for window lifecycle and IPC bridge
- chore(ci): add desktop build matrix for macOS/Windows/Linux

## Test plan

- [ ] `task desktop:dev` launches app window with React frontend loaded
- [ ] `task desktop:build` produces working binary on current OS
- [ ] Existing `task web:dev` still works (no regression)
```

**Repo has a minimal PR template** (just a `# Description` heading) — the `Title:` preamble is added on top regardless, and the body reproduces the template exactly:
```markdown
Title: Fix SSM tunnel teardown and deterministic router selection
---
# Description

Fixes `atun down` leaving SSM sessions dangling instead of closing them server-side, and makes router instance selection deterministic when multiple EC2 instances match discovery tags.

**Changes**

- fix(ssh): send SIGINT instead of SIGTERM so session-manager-plugin ends the session server-side
- fix(tunnel): prefer the oldest running router instance over an unordered/newest pick

**Test plan**

- [ ] `atun up` then `atun down`; confirm the remote session actually closes
```
