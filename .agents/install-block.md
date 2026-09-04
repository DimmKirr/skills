# Install block

Canonical install wording. Copy verbatim into any README that documents installation.

## Claude Code (plugin)

```bash
claude plugin marketplace add dimmkirr/skills
claude plugin install dimmkirr-skills@dimmkirr
```

Installs the promoted set as a managed, read-only bundle that updates when the repo ships.

## Codex, Cursor, and other Agent-Skills-standard agents

```bash
npx skills@latest add dimmkirr/skills
```

Copies editable skill files into your project; pick the skills and target agents interactively. Pull upstream changes later with `npx skills update`.

## Local development (this machine)

```bash
task link
```

Symlinks every skill into `~/.claude/skills` and `~/.agents/skills`; `git pull` keeps them current. Requires [go-task](https://taskfile.dev).
