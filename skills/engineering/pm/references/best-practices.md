# Best Practices

## Code Analysis Strategy
- Start broad with Grep searches for feature keywords
- Narrow to specific files with Glob patterns
- Read implementation files to understand completion
- Check test files to validate functionality

## Context Preservation
- When splitting, copy all relevant context to new ticket
- Include file paths, function names, related tickets
- Add implementation notes from your analysis
- Link to documentation or specs if referenced

## Description Management
- **ALWAYS use markdown checkboxes** `- [ ]` for sub-tasks (REQUIRED)
- Keep descriptions focused on remaining work
- Remove completed items (move to comments if needed for history)
- Mark completed items as `- [x]` before removing or splitting
- Update titles to reflect actual scope after splits

**When updating tickets:**
- Convert bullet lists to checkboxes: `- Item` -> `- [ ] Item`
- Mark completed as checked: `- [ ]` -> `- [x]`
- Split keeps unchecked items in new ticket
- Original ticket shows checked items before removal

## Emoji to Markdown Checkbox Conversion (REQUIRED)

When you encounter status emojis in ticket descriptions, ALWAYS convert them to proper markdown checkboxes:

| Emoji | Markdown | Meaning |
|-------|----------|---------|
| check mark | `- [x]` | Completed/checked |
| cross mark | `- [x]` | Completed (failed/negative) |
| hourglass | `- [ ]` | Not done/pending |
| timer | `- [ ]` | Not done/pending |
| clipboard | `- [ ]` | Not done/to-do |
| checkbox empty | `- [ ]` | Not done/unchecked |
| check mark alt | `- [x]` | Completed/checked |
| ballot box checked | `- [x]` | Completed/checked |

**Before (plain text with emojis):**
```
[check] Phase 1: internal/manifest/ package created
[check] Phase 2: internal/validate/ package created
[pending] Phase 4: Orchestrator split (partial)
```

**After (markdown checkboxes):**
```
- [x] Phase 1: internal/manifest/ package created
- [x] Phase 2: internal/validate/ package created
- [ ] Phase 4: Orchestrator split (partial)
```

## Communication
- Always explain status changes in comments
- Provide clear rationale for splits
- Include next steps in comments
- Use full URLs when linking tickets

## Cross-Team Duplicates (Partially Overlapping)

When a ticket in Team B overlaps with completed work in Team A but has remaining unique items:
- **NEVER mark as a clean duplicate**: this loses the remaining work
- **Extract remaining items** to a new ticket in the **same project** as the original (Team B)
- Mark the original as duplicate only AFTER the new ticket captures all remaining work

**Confidence Levels for Duplicate Judgments:**
- 90%+: Clear overlap, same scope -> safe to mark duplicate
- 70-89%: Significant overlap but scope differs -> prefer split over duplicate
- <70%: Related but distinct -> keep both tickets open
