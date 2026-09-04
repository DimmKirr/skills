# Data Engineering Learnings

This file accumulates patterns, gotchas, and rules discovered during data engineering tasks.
**Read this file at the start of every data engineering session. Append new entries after completing tasks.**

---

## How to Add a Learning

```markdown
### [YYYY-MM-DD] <Short title>

**Context**: What dataset/situation this applies to.
**Finding**: What was discovered (bug, pattern, edge case, naming rule).
**Rule**: The actionable check or transformation to apply going forward.
**Example** (optional): Concrete example of the issue or fix.
```

Keep entries specific and actionable. Prefer "source X exports dates as MM/DD/YYYY" over "be careful with dates."

---

## Learnings

<!-- Append new entries below this line -->

### Entity name mismatches across multi-provider data sources

**Context**: Cross-referencing entity names between two independent data providers where naming conventions differ.

**Finding**: New entities entering the dataset each period bring name variants not in the alias table:
- Formal vs common name ("Deutsche Bundesbank" vs "Bundesbank")
- Umlaut/diacritic normalization yielding different results than English transliteration ("Zürich" → "zurich" vs "Zuerich")
- Different locale conventions ("Praha" vs "Prague" vs "Prag")
- ASCII vs native script with special characters not handled by normalizer ("ğ", "ş", "ø")
- Inconsistent prefix stripping — normalizer strips one common prefix but not others of similar form
- Translated vs canonical local name ("Munich" vs "München")

**Rule**: When extending date range to a new period, run a diagnostic that:
1. Loads matched records from both providers
2. Identifies unmatched records
3. Extracts and normalizes entity names from unmatched records
4. Cross-references against the known alias table

**Rule**: Normalizer prefix stripping must cover all common prefixes in the domain, not just the most frequent one.

**Rule**: Enable date fallback matching for any provider that stores timestamps in local time — cross-provider date mismatches of ±1 day are common when one uses UTC and the other uses local timezone.

### Match rate thresholds for multi-provider datasets

**Context**: Integration tests that validate entity matching rate across providers.

**Finding**: With clean alias coverage and date fallback enabled, match rates typically reach 95-98%. A threshold of 95% is a safe baseline for regression testing.

**Rule**: If match rate drops below 95%, first check for new entity name aliases (localized/translated names), then check for date format or timezone issues.

### Travel evidence must distinguish booking from completed travel

**Context**: Auditing residence-permit proof-of-stay packages assembled from flight and lodging PDFs.

**Finding**: Booking confirmations establish planned dates but do not independently establish that a flight was boarded or lodging was used. Continuous reservation coverage can still contain this evidentiary gap.

**Rule**: Verify both itinerary continuity and completion evidence. Prefer boarding passes or carrier records marked boarded for flights, and final invoices, city-tax receipts, or operator stay confirmations for lodging.

**Rule**: Passport entry and exit stamps matching the itinerary can close the completion-evidence gap when an inbound flight file is only a booking confirmation.

### Registry evidence and applicant declarations serve different purposes

**Context**: Auditing residence-permit investment-maintenance evidence.

**Finding**: A current land-registry certificate proves registered ownership but does not replace an applicant's signed declaration of continued compliance with program conditions.

**Rule**: Check documentary evidence and required declarations separately, even when they support the same application requirement.

### Evidence presence is not upload readiness

**Context**: Auditing online application document folders.

**Finding**: A source archive may contain suitable evidence while the category folder is empty, oversized, expired, duplicated, or not combined in the format accepted by the portal.

**Rule**: Audit each category for four independent states: source evidence exists, evidence is current, evidence proves the requested fact, and the final upload meets the portal's file constraints.
