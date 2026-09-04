---
name: data-engineer
description: "Data quality verification skill for data engineering tasks. Use when working with data files, pipelines, or datasets that require validation. Triggers for: verifying file paths exist and are correct, checking file naming conventions, validating data ranges and types, auditing data quality, inspecting CSV/JSON/Parquet/Excel files, checking for nulls/outliers/duplicates, or any data ingestion and transformation quality checks."
---

# Data Engineer — Quality Verification

## When NOT to use

- Application business logic or domain rules unrelated to data quality
- Frontend rendering or UI component work
- Infrastructure provisioning or deployment (use devops-engineer)
- General code review that doesn't involve data files or pipelines

## Philosophy: Lean on Determinism

**The fundamental data quality strategy is: always prefer deterministic verification over probabilistic inspection.**

This means:

- **CLI tools over reading files** — `jq`, `csvstat`, `duckdb` give exact answers without loading data into context
- **Test suites over manual spot-checks** — a parametrized test with 20 known cases proves correctness; eyeballing 5 rows doesn't
- **Explicit enumeration over sampling** — list every known alias, variant, and edge case in a test table; don't assume coverage from a sample
- **Repeatable commands over one-off analysis** — every check should be a command you can run again identically on the next batch

This approach scales: the same `pytest` suite that validates Munich/München/Muenchen today will catch the next alias added to the source system tomorrow. The same `jq` one-liner that checks date formats works on a 10-row file and a 10M-row file identically.

When in doubt, ask: "Is this check deterministic and repeatable?" If not, make it so.

---

## Core Principle: Never Load Large Datasets into Context

**Always use deterministic CLI tools instead of reading file contents.**

| Step | What to do |
|------|-----------|
| Discover structure | `head -5` / `head -c 2048` to see shape without loading |
| Count rows/size | `wc -l`, `du -sh`, `ls -lh` |
| Spot-check values | `jq`, `mlr`, `csvkit` (`csvstat`, `csvcut`, `csvgrep`) |
| Query JSON | `jq` with filters — never `cat` a large JSON file |
| Query CSV | `csvstat` for stats, `csvcut` for columns, `mlr` for grouping |
| Query Parquet | `parquet-tools head`, `duckdb` inline queries |
| Validate YAML | `python3 -c "import yaml,sys; yaml.safe_load(sys.stdin)"` piped from `head` |

Never use `cat`, `Read`, or open a file fully unless it is confirmed small (<100 lines or <10KB).

## Workflow

When given a data engineering task:

1. **Read learnings first** — Check `references/learnings.md` for known gotchas, patterns, and project-specific rules that apply to the current task.
2. **Probe structure** — Use `head` + format-appropriate tools to understand the dataset without loading it.
3. **Run quality checks** — Apply spot-checks from `references/checks.md` using deterministic CLI commands.
4. **Report findings** — Summarize issues found with severity and suggested fix.
5. **Record new learnings** — After completing any task, append reusable insights to `references/learnings.md`.

## Quick Checks Reference

| Area | When to apply | Reference |
|------|--------------|-----------|
| File paths & names | Always | `references/checks.md` → File Checks |
| Data ranges & types | When inspecting values | `references/checks.md` → Data Checks |
| Schema validation | When structure matters | `references/checks.md` → Schema Checks |
| Data mapping / normalization | When values have aliases, variants, or canonical forms | `references/mapping-tests.md` |
| Project learnings | Always (read first, write after) | `references/learnings.md` |

## Data Mapping: Use Test Frameworks, Not Just CLI Spot-Checks

When a transformation maps input values to canonical forms — city names, country codes, currency symbols, unicode variants, abbreviations — **write deterministic tests with pytest or go test**. CLI spot-checks find what's wrong; test suites prove what's correct and prevent regressions.

Use `pytest.mark.parametrize` or table-driven Go tests to enumerate all known equivalences explicitly:

```python
# Munich has three valid spellings — all must normalize to the same canonical form
@pytest.mark.parametrize("input,expected", [
    ("Munich",   "Munich"),
    ("Muenchen", "Munich"),
    ("München",  "Munich"),
    ("MUNICH",   "Munich"),   # casing variant
    ("munich",   "Munich"),
])
def test_city_normalization(input, expected):
    assert normalize_city(input) == expected
```

See `references/mapping-tests.md` for full patterns (Go, pytest, edge cases).

## Severity Levels

- **CRITICAL** — Data is wrong, missing, or will break downstream. Must fix before proceeding.
- **WARNING** — Data is suspect or non-standard. Investigate before proceeding.
- **INFO** — Observation worth noting, no immediate action required.

## Adding Learnings

After completing a data engineering task, append to `references/learnings.md`:

```markdown
### [YYYY-MM-DD] <Short title>

**Context**: What project/dataset/situation this applies to.
**Finding**: What was discovered (bug, pattern, edge case, naming rule).
**Rule**: The actionable check to apply going forward.
**Example** (optional): Concrete example of the issue or fix.
```

Be specific. Not "be careful with dates" — instead: "source X exports dates as MM/DD/YYYY, not ISO 8601 — always convert on ingest."

## Self-Assessment Checklist

Before presenting output to the user, verify:

- [ ] All referenced file paths verified to exist
- [ ] Data types and ranges validated against schema
- [ ] Null/duplicate/outlier checks completed
- [ ] Sample output reviewed for correctness
