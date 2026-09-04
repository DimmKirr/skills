# Skills

Dmitry Kireev's agent skills — git workflow, debugging, autonomous TDD, and session management. Built on the [Agent Skills standard](https://agentskills.io), so they work in Claude Code, Codex, Cursor, and any other harness that reads `SKILL.md`.

## Installation

### Claude Code (plugin)

```bash
claude plugin marketplace add dimmkirr/skills
claude plugin install dimmkirr-skills@dimmkirr
```

Installs the promoted set as a managed, read-only bundle that updates when the repo ships.

### Codex, Cursor, and other Agent-Skills-standard agents

```bash
npx skills@latest add dimmkirr/skills
```

Copies editable skill files into your project; pick the skills and target agents interactively. Pull upstream changes later with `npx skills update`.

### Local development (this machine)

```bash
task link
```

Symlinks every skill into `~/.claude/skills` and `~/.agents/skills`; `git pull` keeps them current. Requires [go-task](https://taskfile.dev); see `Taskfile.yml` for the other developer tasks (`task list`, `task validate`).

## Reference

All skills below are **user-invoked**: you reach them by typing their name (e.g. `/commit-message`); the model never fires them on its own.

### Engineering

Daily code work.

<!-- skills:engineering:start -->
- **[ai-rebase](./skills/engineering/ai-rebase/SKILL.md)** — Generate improved commit messages for a git commit range using parallel subagents, without creating commits.
- **[continue-debug](./skills/engineering/continue-debug/SKILL.md)** — Analyze the output of the most recent debug run in .scratch/debug/ and iterate with ranked hypotheses.
- **[data-engineer](./skills/engineering/data-engineer/SKILL.md)** — Data quality verification skill for data engineering tasks. Use when working with data files, pipelines, or datasets that require validation. Triggers for: verifying file paths exist and are correct, checking file naming conventions, validating data ranges and types, auditing data quality, inspecting CSV/JSON/Parquet/Excel files, checking for nulls/outliers/duplicates, or any data ingestion and transformation quality checks.
- **[devops-engineer](./skills/engineering/devops-engineer/SKILL.md)** — Use when making infrastructure changes (nix, docker, MCP, terraform) that need validation, when an E2E test is too expensive for the iteration cycle, when you need to isolate a testable concern from a larger integrated system, or when the user asks to run/test something — present the cost/level pyramid BEFORE executing
- **[drawio-diagram](./skills/engineering/drawio-diagram/SKILL.md)** — Use when working with .drawio diagrams — creating new architecture diagrams from scratch, cleaning up layout, analyzing positioning, fixing alignment or spacing issues, editing connectors, checking border overlaps, or any task involving mxGraphModel XML
- **[frontend-qa](./skills/engineering/frontend-qa/SKILL.md)** — Frontend QA workflow for Expo/React Native web apps. Use when asked to: test the app locally, verify all tabs/screens work, check if the OpenAPI schema is current, test API endpoints directly with curl/hurl, do visual QA with Playwright MCP screenshots, assess overall UI quality, or identify missing/broken UI elements. Covers: dev server startup, schema freshness check, direct API testing, Playwright MCP screenshot analysis, visual quality rubric, and critical-thinking checklist for missing elements.
- **[git-group-commit](./skills/engineering/git-group-commit/SKILL.md)** — Group uncommitted changes into feature commits with conventional messages, and emit runnable commit artifacts. Use when the user asks to commit changes, write or improve a commit message, split work into multiple commits, or another skill needs commit messages for uncommitted changes. A single change is handled as one group. Do NOT use for PR descriptions (git-pr-message owns those).
- **[git-pr-message](./skills/engineering/git-pr-message/SKILL.md)** — Generate a pull request description from committed groups and save it to .scratch/PR.md.
- **[implement-tdd-autonomously](./skills/engineering/implement-tdd-autonomously/SKILL.md)** — Implement the agreed work fully autonomously using strict TDD with judgment-call rules and fail-safes. Auto-detects the right verification mode based on context.
- **[ios-qa](./skills/engineering/ios-qa/SKILL.md)** — iOS Visual QA using Go tests + Claude Vision. Runs Go test flows that capture per-step screenshots, then evaluates each screenshot against the app's design system (docs/DESIGN.md) and Linear user story acceptance criteria. Use when asked to: visually QA the iOS app, verify screens look correct, check design compliance, do a visual regression check, or review UI after changes. Prerequisites: - Host Mac running `task ios:dev` (simulator + WDA) - WDA reachable (set WDA_URL env var, or defaults to host.docker.internal:8100)
- **[kitcut-implement](./skills/engineering/kitcut-implement/SKILL.md)** — Reproduce a working application from a kitcut-artifact/2.0 bundle (facts.json + checks.json + requirements/ + digests/; evidence/ optional and verification-only). Use when the user provides an artifact bundle directory and wants the described app rebuilt, reproduced, implemented, or incrementally re-applied after an edit to the bundle. Do NOT use for analyzing/reviewing ordinary source repos or for creating artifacts (that is ingest's job).
- **[pm](./skills/engineering/pm/SKILL.md)** — Project manager for backlog grooming, ticket analysis, and implementation status tracking. Use for analyzing ticket relevance, checking implementation status against codebase, splitting partially-done tickets, managing labels/assignees, and maintaining backlog health.
- **[react-native-blueprint](./skills/engineering/react-native-blueprint/SKILL.md)** — Extract features, API contracts, and design system from React Native / Expo source code. Produces features.md, features.json, and design-system.md for re-implementation. Deterministic detection first, then LLM-enriched analysis.
- **[reverse-wireframe-ui](./skills/engineering/reverse-wireframe-ui/SKILL.md)** — Use when creating wireframe diagrams from existing app screenshots or mockups. Triggers when user provides UI screenshots and wants drawio wireframes, component hierarchy documentation, or visual specs. Also use when reverse-engineering UI structure from images for design handoff, documentation, or re-implementation planning.
- **[tickets-status-update](./skills/engineering/tickets-status-update/SKILL.md)** — Post a structured status update comment (DONE / WORKING ON / BLOCKED ON) to the current ticket in Linear/Jira.
- **[vector-designer](./skills/engineering/vector-designer/SKILL.md)** — Use when creating logos, icons, SVG graphics, or any vector design work requiring visual iteration. Use when user asks to design, draw, animate, or create visual assets like logos, favicons, badges, or diagrams in SVG/PNG format. Use when adding CSS-based logo animations or brand reveal effects.
<!-- skills:engineering:end -->

### Productivity

General workflow tools, not code-specific.

<!-- skills:productivity:start -->
- **[decomposition-reconstruction](./skills/productivity/decomposition-reconstruction/SKILL.md)** — Use when dealing with complex systems that need simplification, identifying bottlenecks or critical failure points, redesigning architecture or processes for better performance, breaking down problems that feel overwhelming, analyzing dependencies to understand ripple effects, user mentions "this is too complex", "where's the bottleneck", "how do we redesign this", "what are the key components", or when optimization requires understanding how parts interact.
- **[linear-worker](./skills/productivity/linear-worker/SKILL.md)** — Use when the user wants to monitor Linear tickets assigned to a user and react to comments, status changes, or stale tickets. Use when setting up a recurring routine or loop that watches Linear for activity and takes action (responds, flags, nudges, summarizes).
- **[markdown-to-pdf](./skills/productivity/markdown-to-pdf/SKILL.md)** — Convert markdown to PDF, create PDF from .md file, render markdown as print-ready document. Use when: "convert markdown to pdf", "create pdf out of this file", "render this as pdf", "make a pdf from markdown", or any request to turn a .md file into a styled PDF document.
- **[pickup](./skills/productivity/pickup/SKILL.md)** — Load .scratch/CONTINUE.md, reconcile it with the workspace, and continue the saved work.
- **[wrapup](./skills/productivity/wrapup/SKILL.md)** — Save current session state to .scratch/CONTINUE.md and prepare for a safe user-controlled exit.
<!-- skills:productivity:end -->

Non-promoted buckets — [misc](./skills/misc/README.md), [in-progress](./skills/in-progress/README.md), [deprecated](./skills/deprecated/README.md) — hold personal, beta, and retired skills that don't ship in the plugin.

## Repo layout

```
skills/<bucket>/<skill-name>/
├── SKILL.md            # frontmatter + instructions (the portable artifact)
├── agents/openai.yaml  # Codex UI metadata (+ invocation policy)
├── references/         # optional: large reference material
└── scripts/            # optional: executable helpers
```

Conventions live in [AGENTS.md](./AGENTS.md); start new skills from [template/](./template/).

## Credits

Repository structure modeled on [mattpocock/skills](https://github.com/mattpocock/skills) (bucketed layout, invocation conventions, plugin packaging) and [anthropics/skills](https://github.com/anthropics/skills) (skill anatomy and marketplace setup).
