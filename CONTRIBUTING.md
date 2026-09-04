# Contributing

## Adding a skill

1. Copy the starter template:
   ```bash
   cp -r template/ skills/<bucket>/<skill-name>/
   ```

2. Edit `SKILL.md`: fill in the YAML frontmatter (`name`, `description`, optionally `disable-model-invocation: true`) and write the instruction body.

3. Edit `agents/openai.yaml`: set `display_name` and `short_description`. For user-invoked skills, add `policy.allow_implicit_invocation: false`. See [.agents/invocation.md](.agents/invocation.md) for details.

4. Add reference material (if any) to `references/` and helper scripts to `scripts/`.

5. Regenerate indexes and validate:
   ```bash
   task sync
   task validate
   ```

6. Submit a PR. CI runs `task validate` and checks that indexes are up to date.

## Buckets

| Bucket | Purpose | Ships in plugin? |
|--------|---------|-----------------|
| `engineering/` | Daily code work | Yes |
| `productivity/` | Non-code workflow tools | Yes |
| `in-progress/` | Beta, feedback wanted | No |
| `misc/` | Personal or rarely used | No |
| `deprecated/` | Retired | No |

Only `engineering/` and `productivity/` are promoted (listed in README.md and plugin.json).

## Conventions

- SKILL.md bodies should stay under 500 lines. Extract large content into `references/`.
- Use `references/` (plural) for reference material, `scripts/` for executables.
- Keep invocation flags in sync across SKILL.md and openai.yaml.
- Use markdown checkboxes (`- [ ]`) for checklists.
- Run `task sync` after any change to skill names, descriptions, or bucket placement.

## Local development

```bash
task link     # symlink skills into ~/.claude/skills and ~/.agents/skills
task list     # enumerate all skills
task validate # check plugin manifests
```

## Code of conduct

Be kind. This is a personal project shared publicly. Issues and PRs are welcome.
