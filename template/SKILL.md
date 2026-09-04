---
name: template-skill
description: Replace with what the skill does. Model-invoked skills keep trigger phrasing ("Use when the user wants…"); user-invoked skills get a human-facing one-liner.
# argument-hint: <what to pass, if the skill takes arguments>
# disable-model-invocation: true   # uncomment for user-invoked (slash-command-style) skills
---

# Replace with instructions

Write the instructions the agent follows when this skill fires.

- Put large reference material in `references/*.md` and link it relatively.
- Put executable helpers in `scripts/`.
- Refer to other skills by prose invocation ("Run the `/other-skill` skill"), never by cross-folder file links.
