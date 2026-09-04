# Data Mapping Tests

When data has aliases, variants, or canonical forms, write deterministic tests — not just CLI spot-checks.
Tests serve as living documentation of what the mapping is supposed to do.

## When to Write Mapping Tests

| Problem | Example | Test approach |
|---------|---------|--------------|
| City/place name variants | Munich / München / Muenchen | parametrize all known aliases |
| Country/currency codes | UK / GB / GBR / United Kingdom | table-driven, include edge cases |
| Unicode normalization | café / cafe / café (different encodings) | include NFC/NFD variants |
| Abbreviations | St. / Street / Str. | exhaustive list from source data |
| Case normalization | GERMANY / germany / Germany | always include UPPER/lower/Title |
| Null/empty representations | "" / "N/A" / "null" / None | explicit null-equivalence cases |
| Date format variants | 01/31/2024 / 2024-01-31 / 31.01.2024 | all formats seen in source |

---

## pytest — Parametrized Mapping Tests

```python
import pytest

# --- City name normalization ---
@pytest.mark.parametrize("raw,expected", [
    # Canonical forms
    ("Munich",    "Munich"),
    ("Berlin",    "Berlin"),
    # Unicode variants
    ("München",   "Munich"),
    ("Köln",      "Cologne"),
    # Transliterations
    ("Muenchen",  "Munich"),
    ("Koeln",     "Cologne"),
    # Casing
    ("MUNICH",    "Munich"),
    ("munich",    "Munich"),
    ("mUnIcH",    "Munich"),
    # Whitespace
    (" Munich ",  "Munich"),
    # Unknown passthrough (decide: raise or passthrough?)
    ("Springfield", "Springfield"),
])
def test_normalize_city(raw, expected):
    assert normalize_city(raw) == expected


# --- Null equivalence ---
@pytest.mark.parametrize("raw", [
    "", " ", "N/A", "n/a", "NA", "null", "NULL", "None", "none", "-", ".",
])
def test_null_values_normalize_to_none(raw):
    assert normalize_null(raw) is None


# --- Currency codes ---
@pytest.mark.parametrize("raw,expected", [
    ("EUR", "EUR"),
    ("€",   "EUR"),
    ("usd", "USD"),
    ("$",   "USD"),
    ("GBP", "GBP"),
    ("£",   "GBP"),
])
def test_normalize_currency(raw, expected):
    assert normalize_currency(raw) == expected
```

### Best Practices for pytest Mapping Tests

- **Name the test after the mapping function**, not the data domain (`test_normalize_city` not `test_data_quality`)
- **Include failure cases** — test that invalid input raises or returns a sentinel, not silently passes
- **Add source annotation** — comment where each variant was found in real data:
  ```python
  ("München",  "Munich"),   # source: German CRM export
  ("Muenchen", "Munich"),   # source: legacy ASCII-only system
  ```
- **Run with `-v` to see each parametrized case** by name
- **Group by mapping concern**, not by file — one test class per normalization function

---

## Go — Table-Driven Mapping Tests

```go
func TestNormalizeCity(t *testing.T) {
    cases := []struct {
        input    string
        expected string
    }{
        {"Munich",    "Munich"},
        {"München",   "Munich"},   // unicode
        {"Muenchen",  "Munich"},   // transliteration
        {"MUNICH",    "Munich"},   // uppercase
        {"munich",    "Munich"},   // lowercase
        {" Munich ",  "Munich"},   // whitespace
        {"Köln",      "Cologne"},
        {"Koeln",     "Cologne"},
    }

    for _, tc := range cases {
        t.Run(tc.input, func(t *testing.T) {
            got := NormalizeCity(tc.input)
            if got != tc.expected {
                t.Errorf("NormalizeCity(%q) = %q, want %q", tc.input, got, tc.expected)
            }
        })
    }
}
```

---

## Discovering Aliases from Real Data

Before writing tests, extract the actual variants present in the dataset:

```bash
# CSV: unique values in a city column (sorted by frequency)
csvcut -c city <file.csv> | sort | uniq -c | sort -rn | head -50

# JSONL: same for a JSON field
jq -r '.city' <file.jsonl> | sort | uniq -c | sort -rn | head -50

# Spot unicode variants (shows hex for non-ASCII chars)
jq -r '.city' <file.jsonl> | sort -u | python3 -c "
import sys, unicodedata
for line in sys.stdin:
    s = line.strip()
    if any(ord(c) > 127 for c in s):
        print(repr(s), [unicodedata.name(c) for c in s if ord(c) > 127])
"
```

Use this output to build the parametrize list — don't guess, enumerate from data.

---

## Red Flags in Mapping Logic

- Mapping is done with `if/elif` chains → hard to test and extend; prefer a lookup dict
- No test for the "unknown input" case → silent data corruption risk
- Tests only cover happy path → unicode/whitespace/case failures will appear in production
- Mapping lives in a pipeline step with no unit test → impossible to verify without running the whole pipeline
