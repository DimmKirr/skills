# Skills

Agent skills for git workflow, debugging, autonomous TDD, and session management. Built on the [Agent Skills standard](https://agentskills.io).

## Must-follow rules

- Indexes are **generated, never hand-edited.** After adding, removing, renaming, or re-describing any skill, run `task sync` then `task validate`. Never edit content between `<!-- skills:...start -->`/`<!-- skills:...end -->` markers directly; fix the skill's frontmatter and re-sync instead.
- Keep invocation flags in sync across both harnesses: `disable-model-invocation: true` in SKILL.md frontmatter must pair with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. See [.agents/invocation.md](./.agents/invocation.md).
- Start new skills from [template/](./template/).
- SKILL.md bodies should stay under 500 lines. Extract large reference material into `references/`.

## Must-read documents

- [.agents/invocation.md](./.agents/invocation.md) — user-invoked vs model-invoked conventions
- [template/SKILL.md](./template/SKILL.md) — skill starter template
- [README.md](./README.md) — installation, full skill list, repo layout

## Commands

| Command | What it does |
|---------|-------------|
| `task list` | Enumerate all skills with their bucket and invocation type |
| `task sync` | Regenerate all skill indexes (bucket READMEs, top-level README, plugin.json) |
| `task link` | Symlink every skill into `~/.claude/skills` and `~/.agents/skills` |
| `task validate` | Check plugin manifests (plugin.json + marketplace.json) |

## Skill anatomy

Each skill is a folder containing `SKILL.md` (YAML frontmatter + instructions), an `agents/openai.yaml` (Codex UI metadata), and optional `references/` and `scripts/` subfolders.

Skills are organized into bucket folders under `skills/`:

- `engineering/` — daily code work (git workflow, debugging, TDD)
- `productivity/` — daily non-code workflow tools (session management, structured opinions)
- `misc/` — kept around but rarely used or personal, not promoted
- `in-progress/` — beta: public on purpose, feedback wanted, not shipped in the plugin
- `deprecated/` — no longer used

Every skill in `engineering/` or `productivity/` (the **promoted** buckets) is listed in the top-level `README.md` and in `.claude-plugin/plugin.json`'s `skills` array (the Claude Code plugin ships exactly the promoted set). Skills in `misc/`, `in-progress/`, and `deprecated/` appear in neither.

Each bucket folder has a `README.md` that lists every skill in the bucket with a one-line description, with the skill name linked to its `SKILL.md`. The top-level `README.md` does the same for the promoted buckets. Both are maintained by `task sync`.

`.claude-plugin/marketplace.json` makes the repo its own single-plugin marketplace.

Every `SKILL.md` is either user-invoked (`disable-model-invocation: true` plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, reachable only by the human) or model-invoked (model- or user-reachable).

These skills replaced the legacy `commands/` directory (Claude Code merged slash commands into skills in January 2026). A skill with `disable-model-invocation: true` behaves exactly like the old slash command.

## Code style

- SKILL.md uses YAML frontmatter (between `---` fences) for metadata: `name`, `description`, `disable-model-invocation`.
- Reference material goes in `references/` (plural). Scripts go in `scripts/`.
- Use XML tags (`<constraints>`, `<examples>`, `<output-format>`) for section boundaries in complex skills to improve model parsing.
- Markdown checkboxes (`- [ ]`) for checklists, not emoji status markers.

## Security

- YAML frontmatter values containing `<` or `>` must be quoted to prevent XML injection into the instruction body.
- Skill instructions are untrusted input to the model. Do not embed secrets, API keys, or credentials in SKILL.md or references/.
