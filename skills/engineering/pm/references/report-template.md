# Phase 7: Grooming Summary Report

**CRITICAL:** After completing grooming, ALWAYS provide a comprehensive summary.

## Report Template

After processing all tickets, provide a structured summary:

```markdown
# Backlog Grooming Summary
**Date:** YYYY-MM-DD
**Scope:** [describe filter: "my tickets", "project X", "all backlog", etc.]
**Tickets Analyzed:** N

## Actions Taken

### WHY Satisfied: Alternative Implementation (N tickets)
Business concern resolved by different approach than described in ticket.

**PROJ-789** - Build mock HTTP server for API testing
- **WHY:** "Develop and test payment flows without hitting production"
- **Resolved by:** `MockPaymentService` in `src/services/payment/mock.ts`
- **Divergence:** Ticket describes HTTP mock server; codebase uses service injection
- **Verification:** Test suite runs without network calls
- **User decision needed:** Close as-is / Keep open / Rewrite WHAT
- **URL:** {ticket.url}

---

### Moved to In Review (N tickets)
Tickets with 100% implementation moved to review status.

**PROJ-123** - User authentication system
- **Action:** Backlog -> In Review
- **Reason:** All 8 core auth features fully implemented
- **Evidence:** src/auth/, src/middleware/auth.ts, src/services/token.ts
- **URL:** {ticket.url}

---

### Split Tickets (N tickets)
Partially implemented tickets split into completed + remaining work.

**PROJ-234** - Checkout flow fixes (60% done)
- **Original:** 5 bug fixes in checkout
- **Split to:** PROJ-567 (remaining 2 issues)
- **Kept in PROJ-234:** 3 fixed issues -> moved to In Review
- **URLs:**
  - Original: {ticket.url}
  - New: {ticket.url}

---

### Sized Tickets (N tickets)
Tickets assessed for complexity and LLM implementation risk.

### Labels Added (N tickets)
Missing bug/feature labels assigned based on ticket content.

### Assignees Set (N tickets)
Unassigned tickets assigned to current user (default).

### Status Corrections (N tickets)
Status updated to match implementation reality. Include staleness duration for In Progress tickets.

### Descriptions Updated (N tickets)
Ticket descriptions cleaned up or enhanced with context.

### Documentation Added (N tickets)
WHY/WHAT/HOW/HOW-TO-TEST structure added to improve ticket clarity.

---

### Requires Confirmation (N tickets)
Actions requiring user approval before proceeding.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total tickets analyzed | N |
| Moved to In Review | N |
| Tickets split | N |
| Labels added | N |
| Assignees set | N |
| Status corrections | N |
| Descriptions updated | N |
| Pending confirmation | N |

## Backlog Health

**Before Grooming:**
- Unlabeled tickets: N (%)
- Unassigned tickets: N (%)
- Incorrect status: N (%)

**After Grooming:**
- Unlabeled tickets: 0 (0%)
- Unassigned tickets: 0 (0%)
- Ready to work: N (%)

## Next Actions

1. **Review PROJ-106** - Confirm marking as Done
2. **Start PROJ-567** - New ticket with remaining work
```

## Report Format Rules

1. **Always include ticket numbers** (e.g., PROJ-123)
2. **ALWAYS include FULL ticket URLs** for EVERY ticket mentioned
   - Format: `**URL:** {ticket.url}`
   - Use the `.url` property from ticket objects returned by your ticketing tool
3. **Always explain the reason** for each action taken
4. **Always provide evidence** when available (file paths, test results)
5. **Group actions by type** (moved, split, labeled, assigned, etc.)
6. **Include before/after metrics** to show improvement
7. **List pending confirmations** separately at the end
8. **Provide next actions** so user knows what to do

## Confirmation Required (User Must Approve)

**1. Moving from Review -> Done**
- **Ask**: "PROJ-123 is in Review. Mark as Done?"
- **Wait for**: User confirmation (yes/no)
- **If yes**: `pm.update_ticket` with `state: "Done"`

**2. Deleting/Archiving Duplicates**
- **Ask**: "PROJ-123 is a duplicate of PROJ-456. Archive PROJ-123?"
- **Wait for**: User confirmation
- **If yes**: Archive ticket

**3. Won't Implement (Business Decision)**
- **Ask**: "PROJ-123 no longer needed per business priorities. Archive as Won't Implement?"
- **Wait for**: User confirmation
- **If yes**: Update status to "Cancelled" or "Won't Implement"
