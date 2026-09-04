# Model-invoked vs user-invoked

Every `SKILL.md` in this repo is a skill. The one axis that splits them is **invocation** — who can reach it:

- **User-invoked** — reachable **only by the human typing its name** (e.g. `/commit-message`). Set `disable-model-invocation: true` in the frontmatter (Claude Code) and `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex). The `description` is **human-facing**: a one-line summary read by a person browsing slash-commands. Strip trigger lists ("Use when the user says…").
- **Model-invoked** — reachable by **model or user**. The default: omit `disable-model-invocation` and the `policy` block from `agents/openai.yaml`. The `description` is **model-facing** and keeps rich trigger phrasing ("Use when the user wants…, mentions…, asks for…") so auto-invocation fires. The test for whether a skill should stay model-invoked: _could the model usefully reach for this autonomously?_

Keep the two harness flags in sync: a skill is user-invoked in both harnesses or neither.

Every skill carries an `agents/openai.yaml` beside its `SKILL.md`. It holds Codex UI metadata — `interface.display_name` and `interface.short_description` for the skill picker — and, for user-invoked skills, the `policy.allow_implicit_invocation: false` that pairs with `disable-model-invocation`.

All skills migrated from the legacy `commands/` directory started life as slash commands and are therefore user-invoked. Promote one to model-invoked only after rewriting its `description` to be model-facing.

## Dependencies between skills

Dependencies are expressed as **`/skill`-style prose invocation** ("Run the `/commit-message` skill"), not deep `../other-skill/FILE.md` cross-references. Shared reference docs live inside the skill that owns them (its `references/` folder); other skills reach that material by invoking the skill, not by linking across folders.
