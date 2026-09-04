---
name: ios-qa
description: >
  iOS Visual QA using Go tests + Claude Vision. Runs Go test flows that capture
  per-step screenshots, then evaluates each screenshot against the app's design
  system (docs/DESIGN.md) and Linear user story acceptance criteria. Use when
  asked to: visually QA the iOS app, verify screens look correct, check design
  compliance, do a visual regression check, or review UI after changes.

  Prerequisites:
  - Host Mac running `task ios:dev` (simulator + WDA)
  - WDA reachable (set WDA_URL env var, or defaults to host.docker.internal:8100)
---

# iOS Visual QA

## When NOT to use

- Web app QA (use frontend-qa with Playwright MCP)
- Android app QA
- Unit testing Swift/Objective-C code without visual verification
- Backend API testing that doesn't involve the iOS UI

## Overview

Visual QA is a two-phase process:

1. **Run Go tests** — deterministic flows using gowda element selectors, capturing screenshots at each step
2. **Evaluate screenshots** — read each image with Claude Vision, verify against DESIGN.md and Linear story acceptance criteria

## Phase 1: Run Go Tests

### Setup

```bash
export PATH="/opt/devcell/.local/share/mise/installs/go/1.26.0/bin:$PATH"
export WDA_URL="${WDA_URL:-http://host.docker.internal:8100}"
```

### Run tests

Run specific test or all tests. Each test saves numbered screenshots to `tests/results/<timestamp>-<TestName>/`.

```bash
# Run a specific flow
go test ./tests/ -run TestLoginFlow -v

# Run all flows
go test ./tests/ -v

# Run from Docker
WDA_URL=http://host.docker.internal:8100 go test ./tests/ -v
```

### Available tests

Each test maps to a Linear user story:

| Test | Story | What it covers |
|------|-------|----------------|
| `TestLoginFlow` | KIWA-372 | Empty screen → error → fill fields → sign in → Explore |
| `TestLoginEmptyUsername` | KIWA-372 | Validation error on empty submit |
| `TestBrowseGuidesAndTrips` | KIWA-373 | Guides list → scroll → Trips tab → scroll → back |
| `TestViewGuideDetail` | KIWA-374 | Tap guide → detail sheet → scroll → dismiss |
| `TestSignOut` | KIWA-375 | Sign out → back to login |

### Screenshot output

Tests save screenshots to `tests/results/<timestamp>-<TestName>/`:

```
tests/results/2026-07-16T14-30-00-TestLoginFlow/
├── 01-login-empty.png
├── 02-login-error.png
├── 03-login-fill-username.png
├── 04-login-fill-password.png
└── 05-login-signed-in.png
```

## Phase 2: Visual QA Evaluation

After tests complete, evaluate each screenshot.

### Step 1: Find the results directory

```bash
ls -td tests/results/*/ | head -5
```

Pick the most recent run for the test(s) you want to evaluate.

### Step 2: Read each screenshot

Use the **Read tool** to view each PNG file in order. For each screenshot, evaluate against the checklist below.

### Step 3: Load acceptance criteria

Read the Linear story for the test being evaluated (story ID is in the test comment). Use `get_issue` to fetch acceptance criteria. Compare each screenshot against the relevant acceptance criteria.

### Step 4: Evaluate against DESIGN.md

Read `docs/DESIGN.md` for design system reference. For each screenshot check:

**Layout** (DESIGN.md → Spacing & Layout)
- Elements properly aligned, no overlaps or clipping
- Content respects safe areas (top ~59pt, bottom ~34pt on iPhone 16)
- Spacing follows 8pt grid (4, 8, 12, 16, 20, 24, 32)
- Screen-edge padding: 20px
- Between cards: 12px, card internal padding: 16px

**Typography** (DESIGN.md → Typography)
- Large Title: 34px bold for screen titles
- Headline: 17px semibold for card titles
- Body: 17px regular for reading text
- Caption: 12-13px for metadata, tags
- Clear hierarchy, no truncated titles

**Colors** (DESIGN.md → Color System)
- Accent blue (#007AFF) ONLY on interactive elements
- Error text in red, never blue
- Tag/pill backgrounds: accent at 8% opacity
- Sufficient contrast

**Liquid Glass** (DESIGN.md → Liquid Glass)
- Glass on navigation chrome ONLY (toolbars, tab bars)
- NO glass on cards or content areas
- No nested glass

**Cards** (DESIGN.md → Components → Cards)
- Opaque background (NOT glass/material)
- 12px radius, 16px padding
- No nested cards

**Interactive Elements** (DESIGN.md → Components → Buttons)
- Tap targets >= 44x44pt
- Primary buttons: accent-colored, 50px tall

**iOS Conventions**
- Status bar visible
- Large title navigation pattern
- No Android/Material elements
- Home indicator area respected

### Step 5: Report

Produce a summary report after evaluating all screenshots:

```markdown
## Visual QA Report — <timestamp>

### Tests Evaluated
- [x/fail] TestName (KIWA-xxx): N screenshots, M issues

### Screenshots
| # | Test | Step | File | Result |
|---|------|------|------|--------|
| 1 | TestLoginFlow | login-empty | 01-login-empty.png | pass |
| ... |

### Issues Found
1. [test/step] [critical/warning/nit] Description
   - Expected: ... (reference DESIGN.md section or story AC)
   - Actual: ...
   - Screenshot: filename.png

### Acceptance Criteria Status
- KIWA-372: X/Y criteria met
- KIWA-373: X/Y criteria met
- ...

### Summary
X tests, Y screenshots. A issues (B critical, C warnings, D nits).
```

Save to `tests/results/<run-dir>/report.md`.

## Self-Assessment Checklist

Before presenting output to the user, verify:

- [ ] All test flows ran to completion
- [ ] Every screenshot evaluated against DESIGN.md
- [ ] Acceptance criteria from Linear story checked
- [ ] No WDA connection failures during test run

## Design System Reference

| What | File |
|------|------|
| **App design doc (primary)** | `docs/DESIGN.md` |
| Typography tokens | `design/system/tokens/typography.json` |
| Colors (79 vars x 4 modes) | `design/system/tokens/colors.json` |
| Spacing / radii | `design/system/tokens/spacing.json` |
| Component specs (36) | `design/system/components/specs/` |
| SwiftUI screens | `ios/Screens/*.swift` |
| Go test source | `tests/ios_test.go` |

## Examples

**User:** "QA the login flow"
**Skill does:** Runs `go test ./tests/ -run TestLoginFlow -v`, captures 4 screenshots (empty form, validation error, loading state, success), evaluates each against DESIGN.md, finds submit button is 38pt tall (below 44pt minimum), reports as critical issue.

**User:** "Visual regression check after the tab bar changes"
**Skill does:** Runs all test flows, captures screenshots, compares against DESIGN.md Liquid Glass section, finds glass effect incorrectly applied to a content card (should be navigation chrome only), reports with screenshot reference.
