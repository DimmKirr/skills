# Data Quality Checks

All checks use deterministic CLI tools. Never load full file contents into context.

---

## Step 0: Probe Structure First

```bash
# Any file — size and type
ls -lh <file>
file <file>

# First N bytes/lines to understand format
head -5 <file.csv>
head -c 2048 <file.json>

# Line/record count without reading content
wc -l <file.csv>

# Directory overview
ls -lh <dir>/
du -sh <dir>/
```

---

## File Checks

### Path & Existence
```bash
# Exists?
test -f <path> && echo OK || echo MISSING

# Broken symlink?
file <path>

# Empty?
test -s <path> && echo "has content" || echo "EMPTY"
```

### File Naming
Flag these patterns (inspect with `ls`):
- Spaces in names → breaks shell pipelines
- Dates not in `YYYYMMDD` or `YYYY-MM-DD` format
- Mixed casing in same directory (`SalesData.csv` + `sales_data.csv`)
- `_final`, `_FINAL`, `_v2_FIXED` suffixes → not versioned properly
- Special chars: `()`, `&`, `#`, `@`

### File Integrity
```bash
# Not zero bytes
wc -c <file>

# CSV: last line looks complete (no partial row)
tail -2 <file.csv>

# JSON: valid and not truncated
tail -c 100 <file.json>          # should see closing ] or }
python3 -c "import json,sys; json.load(open('$FILE'))" 2>&1 | head -3

# Encoding — detect BOM or non-UTF-8
file <file>
head -c 3 <file> | xxd           # BOM = ef bb bf
```

---

## Data Checks — CSV

```bash
# Column names + basic stats (counts, nulls, min/max, unique)
csvstat <file.csv>

# Just headers
head -1 <file.csv>
csvcut -n <file.csv>             # numbered column list

# Sample rows for a specific column
csvcut -c <col_name> <file.csv> | head -20

# Null/empty check for a column
csvcut -c <col> <file.csv> | grep -c "^$"

# Unique values in categorical column (spot-check enum)
csvcut -c <col> <file.csv> | sort | uniq -c | sort -rn | head -20

# Duplicate rows
sort <file.csv> | uniq -d | head -10

# Duplicate on key column
csvcut -c <id_col> <file.csv> | sort | uniq -d | head -10

# Row count
wc -l <file.csv>                 # subtract 1 for header
```

---

## Data Checks — JSON / JSONL

```bash
# Structure of first record
head -1 <file.jsonl> | jq .
head -c 2048 <file.json> | jq 'if type=="array" then .[0] else . end'

# Keys of first record
head -1 <file.jsonl> | jq 'keys'

# Check a specific field across all records (JSONL)
jq -r '.<field>' <file.jsonl> | sort | uniq -c | sort -rn | head -20

# Count nulls in a field
jq -r '.<field> // "NULL"' <file.jsonl> | grep -c "^NULL$"

# Min/max of a numeric field
jq -r '.<field> | numbers' <file.jsonl> | sort -n | head -1   # min
jq -r '.<field> | numbers' <file.jsonl> | sort -rn | head -1  # max

# Record count (JSONL)
wc -l <file.jsonl>

# Record count (JSON array)
jq 'length' <file.json>
```

---

## Data Checks — Parquet

```bash
# Schema + row count
parquet-tools schema <file.parquet>
parquet-tools rowcount <file.parquet>

# First few rows as JSON
parquet-tools head -n 5 <file.parquet>

# DuckDB one-liner (most flexible, installed more widely)
duckdb -c "SELECT * FROM '<file.parquet>' LIMIT 5"
duckdb -c "DESCRIBE SELECT * FROM '<file.parquet>'"
duckdb -c "SELECT COUNT(*) FROM '<file.parquet>'"
duckdb -c "SELECT MIN(<col>), MAX(<col>), COUNT(*) FROM '<file.parquet>'"
```

---

## Data Checks — YAML / TOML / Config Files

```bash
# Validate YAML (don't load full file)
python3 -c "import yaml,sys; yaml.safe_load(sys.stdin)" < <file.yaml> 2>&1

# Spot-check keys
python3 -c "import yaml,sys; d=yaml.safe_load(sys.stdin); print(list(d.keys()))" < <file.yaml>

# TOML
python3 -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" <file.toml>
```

---

## Range & Type Spot-Checks

```bash
# Numeric range (CSV column)
csvcut -c <col> <file.csv> | tail -n +2 | sort -n | head -1   # min
csvcut -c <col> <file.csv> | tail -n +2 | sort -rn | head -1  # max

# Date format check — show distinct formats found
csvcut -c <date_col> <file.csv> | tail -n +2 | head -100 | \
  python3 -c "
import sys
from collections import Counter
dates = [l.strip() for l in sys.stdin]
print(Counter(len(d) for d in dates))  # quick format length distribution
"

# Type anomaly — numeric column with strings
csvcut -c <col> <file.csv> | tail -n +2 | grep -v '^[0-9.eE+-]*$' | head -10
```

---

## Schema Checks

```bash
# Compare headers between two CSV files
diff <(head -1 file_a.csv) <(head -1 file_b.csv)

# Check column count consistency (all rows same number of fields)
awk -F',' '{print NF}' <file.csv> | sort | uniq -c

# JSON: check all records have same keys
jq -r 'keys | join(",")' <file.jsonl> | sort | uniq -c | sort -rn | head -5
```

---

## Reporting Template

```
## Data Quality Report — <dataset/file name>

**Checked**: YYYY-MM-DD
**Rows**: X  |  **Columns**: Y  |  **File size**: Z

### CRITICAL
- [ ] <Issue> — <suggested fix>

### WARNING
- [ ] <Issue> — <suggested fix>

### INFO
- [ ] <Observation>
```
