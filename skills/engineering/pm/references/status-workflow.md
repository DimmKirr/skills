# Status Workflow

Visual guide to ticket workflow states and transitions for the `pm` skill.

## Standard Workflow States

```
┌──────────┐
│ Backlog  │  Not planned, future work
└────┬─────┘
     │
     │ Sprint planning
     ▼
┌──────────┐
│   Todo   │  Planned for current sprint
└────┬─────┘
     │
     │ Developer starts work
     ▼
┌──────────────┐
│ In Progress  │  Active development
└────┬─────────┘
     │
     │ Code complete
     ▼
┌───────────┐
│ In Review │  Code review / QA
└────┬──────┘
     │
     │ Approved & merged
     ▼
┌──────────┐
│   Done   │  Completed & deployed
└──────────┘

  (Alternative)
┌────────────┐
│ Cancelled  │  Won't implement
└────────────┘
```

## State Descriptions

### Backlog
**Purpose:** Unprioritized work, future ideas, nice-to-haves

**Characteristics:**
- No assignee required
- No sprint assigned
- No planned start date
- May stay here for weeks/months

**Entry:** Created → Backlog (default)
**Exit:** Sprint planning → Todo

**Grooming Actions:**
- Verify still relevant (or propose archival)
- Ensure has bug/feature label
- Check if accidentally already implemented

### Todo
**Purpose:** Committed work for current sprint or iteration

**Characteristics:**
- Has assignee
- Included in active sprint/cycle
- Ready to start (no blockers)
- Should start within days

**Entry:** Backlog → Todo (sprint planning)
**Exit:** Todo → In Progress (work starts)

**Grooming Actions:**
- Verify has assignee
- Check for blockers
- Ensure clear description
- Validate sprint assignment

### In Progress
**Purpose:** Active development work

**Characteristics:**
- Has assignee (required)
- Work actively happening
- Shouldn't stay here > 1-2 weeks
- May have linked branch/PR

**Entry:** Todo → In Progress (work starts)
**Exit:** In Progress → In Review (code complete)

**Grooming Actions:**
- Check if really in progress (or stale)
- Verify implementation status
- Split if partially done
- Move to Review if 100% implemented

**Warning Signs:**
- In Progress > 2 weeks → Check if stale
- No recent updates → Ask assignee for status
- No linked branch → Verify work started

### In Review
**Purpose:** Code complete, awaiting review/QA/approval

**Characteristics:**
- Has assignee
- Code is complete
- Usually has linked PR
- Waiting for reviewer action
- Should have clear acceptance criteria

**Entry:** In Progress → In Review (code complete)
**Exit:**
- In Review → Done (approved & merged)
- In Review → In Progress (changes requested)

**Grooming Actions:**
- Verify code is actually complete
- Check if PR exists and is ready
- Ensure reviewer assigned
- Check for review feedback

**Confirmation Required:**
- Moving to Done requires user confirmation
- Ensures code was actually reviewed/merged

### Done
**Purpose:** Work completed, reviewed, and deployed

**Characteristics:**
- Has assignee (preserved)
- Code merged to main
- Usually deployed to production
- Ticket archived from active work

**Entry:** In Review → Done (after approval)
**Exit:** None (terminal state)

**Grooming Actions:**
- Verify actually deployed
- Check if follow-up tickets needed
- Document learnings in comments

### Cancelled / Won't Implement
**Purpose:** Work we've decided not to do

**Characteristics:**
- Not implemented
- Decision made not to pursue
- Reasons documented in comments
- Preserved for historical record

**Entry:** Any state → Cancelled (business decision)
**Exit:** None (terminal state)

**Grooming Actions:**
- Requires user confirmation
- Document reason in comment
- Link to replacement ticket if applicable

## Grooming Decision Tree

```
For each ticket:

1. Check implementation in codebase
   │
   ├─ 100% implemented
   │  └─> Move to "In Review"
   │      └─> Add comment: "Implementation complete"
   │
   ├─ 1-99% implemented
   │  └─> Split ticket
   │      ├─> Old ticket → "In Review" (completed work)
   │      └─> New ticket → "Todo" (remaining work)
   │
   └─ 0% implemented
      │
      ├─ Status is "In Progress" + no recent updates
      │  └─> Move to "Todo"
      │      └─> Add comment: "No recent progress, moving back to Todo"
      │
      ├─ Status is "In Review" + no PR
      │  └─> Move to "In Progress"
      │      └─> Add comment: "Code not ready for review"
      │
      ├─ Status is "Done" + not implemented
      │  └─> Move to "In Progress"
      │      └─> Add comment: "Reopening - implementation not found"
      │
      └─ Status is "Backlog" or "Todo" (correct)
         └─> Verify labels, assignee, description
```

## Auto vs Manual Transitions

### ✅ Automatic (No Confirmation)

**To In Review:**
- When: 100% of ticket implemented
- Action: Auto-move + add comment
- Reason: Clear evidence in codebase

**From Backlog → Todo:**
- When: Assigning to sprint
- Action: Auto-move
- Reason: Simple planning operation

**From Todo → In Progress:**
- When: Work starts
- Action: Auto-move
- Reason: Clear intent to start

**Status corrections (mismatches):**
- When: Status doesn't match reality
- Action: Auto-correct + add comment
- Reason: Objective analysis

### ⚠️ Requires Confirmation

**🚨 CRITICAL: NEVER MOVE TO DONE WITHOUT USER APPROVAL 🚨**

**To Done:**
- When: Moving from In Review → Done
- **ALWAYS REQUIRED:** User must explicitly confirm before marking as Done
- Confirmation: "PROJ-123 is in Review. Mark as Done?"
- Reason: Final approval, ensure code was reviewed and merged
- **NEVER automatic** - even if code is merged, user must approve

**To Cancelled:**
- When: Business decision not to implement
- Confirmation: "PROJ-123 no longer needed. Archive as Won't Implement?"
- Reason: Irreversible business decision

**Archival/Deletion:**
- When: Duplicate or obsolete ticket
- Confirmation: "PROJ-123 is duplicate of PROJ-456. Archive?"
- Reason: Permanent removal from backlog

## Common Status Issues

### Issue: Zombie Tickets

**Symptoms:**
- Status: "In Progress"
- Last updated: > 14 days ago
- No branch/PR activity

**Fix:**
```typescript
// Check implementation
const implementation = analyzeCodebase(ticket)

if (implementation.complete === 0) {
  // No work found
  await update_issue({ id, state: "Todo" })
  await create_comment({
    issueId: id,
    body: "No recent progress detected. Moving back to Todo. Please update when resuming work."
  })
} else if (implementation.complete === 100) {
  // Actually done!
  await update_issue({ id, state: "In Review" })
  await create_comment({
    issueId: id,
    body: "Implementation found to be complete. Moving to In Review."
  })
}
```

### Issue: Shadow Completion

**Symptoms:**
- Status: "Backlog" or "Todo"
- Codebase shows fully implemented

**Fix:**
```typescript
await update_issue({ id, state: "In Review" })
await create_comment({
  issueId: id,
  body: `Implementation complete - found in codebase:

  ✅ All 5 features implemented
  - Login: src/auth/login.ts
  - Logout: src/auth/logout.ts
  ...

  Moving to In Review. Please create PR if not done yet.`
})
```

### Issue: Premature Done

**Symptoms:**
- Status: "Done"
- Code analysis shows incomplete

**Fix:**
```typescript
await update_issue({ id, state: "In Progress" })
await create_comment({
  issueId: id,
  body: `Reopening - implementation incomplete:

  ✅ Completed (3/5):
  - Feature A
  - Feature B
  - Feature C

  ⏳ Not implemented (2/5):
  - Feature D
  - Feature E

  Moving back to In Progress.`
})
```

### Issue: Review Without PR

**Symptoms:**
- Status: "In Review"
- No linked PR
- Git shows no branch

**Fix:**
```typescript
await update_issue({ id, state: "In Progress" })
await create_comment({
  issueId: id,
  body: "Moving back to In Progress - no PR found. Please create PR when code is ready for review."
})
```

## State Metadata

### Backlog
- **Type:** `unstarted`
- **Color:** Gray
- **Icon:** 📋
- **Typical duration:** Indefinite

### Todo
- **Type:** `unstarted`
- **Color:** Blue
- **Icon:** 📝
- **Typical duration:** Days to 1-2 weeks

### In Progress
- **Type:** `started`
- **Color:** Yellow
- **Icon:** ⚡
- **Typical duration:** 1-7 days

### In Review
- **Type:** `started`
- **Color:** Orange
- **Icon:** 👀
- **Typical duration:** 1-3 days

### Done
- **Type:** `completed`
- **Color:** Green
- **Icon:** ✅
- **Typical duration:** N/A (terminal)

### Cancelled
- **Type:** `canceled`
- **Color:** Red
- **Icon:** ❌
- **Typical duration:** N/A (terminal)

## Getting Team's Status Names

Different teams may use different status names. Always check:

```typescript
// Get valid status names for the team
const statuses = await pm.list_statuses({
  team: "Engineering"
})

// Find the "In Review" equivalent
const reviewStatus = statuses.find(s =>
  s.type === "started" &&
  s.name.toLowerCase().includes("review")
)

// Use the actual status name
await pm.update_ticket({
  id: ticketId,
  state: reviewStatus.name  // e.g., "In Review", "PR Review", "Code Review"
})
```

## Best Practices

1. **Always add comments when changing status**
   - Explain why status changed
   - Provide evidence (files, functions)
   - Include next steps

2. **Use consistent terminology**
   - Check team's actual status names
   - Don't assume "In Review" exists
   - Use pm.list_statuses first

3. **Respect workflow order**
   - Don't skip states (Backlog → Done)
   - Follow logical progression
   - Exception: corrections based on evidence

4. **Document status changes**
   - Comment on every status change
   - Include rationale and evidence
   - Link to PRs/commits when relevant

5. **Handle edge cases gracefully**
   - Stale tickets: Don't just leave them
   - Premature completion: Reopen with context
   - Zombie tickets: Investigate before moving
