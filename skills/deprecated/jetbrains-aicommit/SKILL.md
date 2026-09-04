---
name: jetbrains-aicommit
description: Prompt template for the JetBrains AI commit message feature (conventional commits). Not an agent workflow.
disable-model-invocation: true
---

Write a commit message in the conventional commit convention.
Lines must not be longer than 74 characters.
Use {locale} language.

{Use this hint to improve the commit message: $hint}

Output ONLY the raw commit message text — no explanations, no
analysis, no markdown, no code fences, no extra sections.

---

## Rules

### Header (first line)

- If the branch name contains a ticket ID (e.g. `ABC-166`, `PROJ-42`),
  end the header with the ID in parentheses: `(ABC-166)`.
- The header must answer "what changed for the user?" — not
  "what code changed".
  Bad:  "Fix stale image detection"
  Good: "cell no longer silently runs outdated containers after a failed build"
- Focus on API/behaviour/user-visible changes. Omit internal refactors
  from the header.

### Bullet list (body)

Every changed area gets one `-` bullet in conventional commit format:

  - feat(scope): what changed — user/api/integration impact
  - fix(scope): what changed — user/api/integration impact
  - refactor(scope): what changed — no user-facing impact
  - test(scope): what changed
  - chore(scope): what changed

Rules:
- Every bullet must have a parenthesized scope.
  `test:` is invalid; use `test(runner):` or `test(cfg):`.
- The part after the em-dash describes the consequence, not the
  mechanism. If it restates the change in different words, rewrite it.
- `chore` and `test` bullets get a short impact note — don't inflate.
- Do NOT include speculative or future changes — only what is in the diff.

---

Branch: {branch}

Previous commit messages (use for style reference only):
{previousCommitMessages}

{diff}
