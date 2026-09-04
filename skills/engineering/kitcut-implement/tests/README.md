# How kitcut-implement is tested

This `tests/` directory is **dev-only**. It is never referenced by SKILL.md,
is not part of the shipped skill anatomy (SKILL.md / scripts / references /
evals), and consumers of the skill never see or run it.

## Execution model

Everything runs **inside an interactive Claude session** following the
skill-creator TDD methodology (evals before prose, pytest before code).
There is deliberately **no `claude -p` harness, no host CI, no cron** —
the session drives all layers (project decision, 2026-08-17).

| Layer | What | Executor | Model? |
|---|---|---|---|
| pytest (`tests/test_kit.py`) | deterministic behavior of `scripts/kit.py` | `python3 -m pytest` via Bash in-session | no |
| `kit.py verify` L1/L2 | build/test/stdout/symbol/token/selector checks | subprocess, invoked by kit.py | no |
| `evals/evals.json` + E2E | skill behavior (activation, loop, edit delta) | live Claude session grading assertions | yes |
| verify L3/L4 | screenshot similarity, acceptance vs requirements | live session judging kit.py's emitted items | yes |

## Running the deterministic suite

```bash
# from the skill directory
python3 -m pytest tests/ -v
```

Requirements: Python 3.10+ with pytest; Go toolchain on PATH (the verify
tests execute `go build` / `go test` / `go run` against the F1 fixture's
evidence). No network, no API keys.

## Fixtures

Tests read (never write) the reference bundles under
`apps/kitcut/test/results/` in the kirr.dev monorepo:

- **F1** `2026-08-17T07-50-44Z-go-helloworld-kitcut-v2` — repo-mode, minimal
- **F2** `2026-08-17T07-40-18Z-kitcut-v2-example` — web-mode (carrot.labs), migrated

Tests that need to corrupt or edit a bundle copy it to `tmp_path` first.

## Failure protocol

Every E2E/eval failure becomes either a pytest case here (script bug) or a
SKILL.md prose fix (loop bug) — committed before retrying. No ad-hoc patches.
