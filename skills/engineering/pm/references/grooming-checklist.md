# Backlog Grooming Checklist

Comprehensive checklist for evaluating ticket health during grooming sessions.

## Per-Ticket Checklist

### 📏 Sizing (Complexity & LLM Risk)

**Check:**
- [ ] Assessed ticket size based on LLM implementation risk (primary)
- [ ] Considered complexity and time estimate (secondary)
- [ ] Counted moving pieces (files, systems, integrations)
- [ ] Evaluated if LLM will struggle with context/coordination
- [ ] Applied size: 1=S, 2=M, 3=L, 4=XL

**Sizing Criteria (Primary: LLM Risk):**

**1 (S - Small)** - Low LLM risk, 1-2 hours
- Single file or closely related files
- Straightforward logic LLM can handle easily
- Minimal context switching

**2 (M - Medium)** - Moderate LLM risk, 2-8 hours
- 2-5 files, related functionality
- LLM can track context across files
- Some coordination needed but manageable

**3 (L - Large)** - Higher LLM risk, 1-3 days
- 5-10 files, multiple components
- LLM needs careful orchestration
- Multiple subsystems but related domain

**4 (XL - Extra Large)** - HIGH LLM risk, 3+ days
- 10+ files, multiple unrelated subsystems
- LLM will struggle with context/coordination
- **Auto-split into smaller tickets**

**Actions:**
- S/M/L: Apply size to ticket
- XL: Automatically decompose into multiple M/L tickets
- Adjust size if implementation status changes estimate

**Example:**
```typescript
await pm.update_ticket({
  id: ticketId,
  estimate: 2  // 1=S, 2=M, 3=L, 4=XL
})
```

---

### ✅ Implementation Status

**Check:**
- [ ] Analyzed codebase for implementation evidence
- [ ] Calculated completion percentage (0%, 1-99%, 100%)
- [ ] Documented what's implemented and what's not
- [ ] Identified relevant files and code locations
- [ ] Noted any partial implementations or tech debt

**Actions:**
- 100% done → Move to "In Review"
- 1-99% done → Split ticket
- 0% done → Verify status is "Backlog" or "Todo"

**Documentation:**
```markdown
Implementation Status: X% complete

✅ Completed:
- [Item 1] - file.ts:10-20
- [Item 2] - other.ts:30-40

⏳ Not implemented:
- [Item 3]
- [Item 4]
```

---

### 🏷️ Labels

**Check:**
- [ ] Has at least one type label ("bug" or "feature")
- [ ] Has appropriate priority label (if team uses them)
- [ ] Has area/component labels (if applicable)
- [ ] Labels match ticket content

**Label Detection:**
- **Bug indicators:** "fix", "error", "broken", "crash", "not working", "issue"
- **Feature indicators:** "add", "implement", "create", "build", "new", "support"

**Actions:**
- Missing type label → Add "bug" or "feature"
- Wrong labels → Update to match actual content
- Over-labeled → Remove irrelevant labels

**Example:**
```typescript
// Before
labels: []

// After
labels: ["bug", "checkout", "p1"]
```

---

### 📝 Description

**Check:**
- [ ] Description is clear and actionable
- [ ] No completed items in "Todo" status tickets
- [ ] Requirements/tasks are specific (not vague)
- [ ] Technical context provided (APIs, files, dependencies)
- [ ] Acceptance criteria defined

**Quality Criteria:**

**Good Description:**
```markdown
# Add password reset flow

## Requirements
- [ ] POST /auth/reset-password endpoint
- [ ] Send reset email with token
- [ ] Token expires in 1 hour
- [ ] Update password on valid token

## Context
- Email service: src/services/email.ts
- Auth routes: src/routes/auth.ts
- Token generation: src/utils/token.ts

## Acceptance Criteria
- User receives reset email within 2 minutes
- Reset link works from email
- Old passwords don't work after reset
```

**Bad Description:**
```markdown
# Fix auth stuff

Users can't log in sometimes. Need to fix it.
```

**Actions:**
- Vague description → Ask product owner for clarification
- Completed items listed → Remove or split ticket
- Missing context → Add technical details from code analysis
- No acceptance criteria → Add specific success conditions

**WHY/WHAT/HOW/HOW-TO-TEST Check (REQUIRED):**

Every ticket MUST have clear structure:

- **WHY**: Business context, problem statement, user impact
- **WHAT**: Requirements (use markdown checkboxes `- [ ]`)
- **HOW**: Technical approach, implementation details, file paths
- **HOW-TO-TEST**: Acceptance criteria (use markdown checkboxes `- [ ]`)

**Detection:**
```markdown
# Missing sections (❌)
Add user authentication
We need login functionality.

# Complete structure (✅)
Add user authentication

## WHY
Users need secure access to their accounts. Currently no authentication
prevents us from personalizing content and protecting user data.

## WHAT
- [ ] Email/password login
- [ ] JWT token generation
- [ ] Protected routes

## HOW
- Use bcrypt for password hashing (src/utils/crypto.ts)
- JWT tokens expire after 24h (src/services/token.ts)
- Middleware: src/middleware/auth.ts
- Store sessions in Redis

## HOW-TO-TEST
- [ ] User can register with email/password
- [ ] User can login and receive JWT token
- [ ] Protected routes return 401 without valid token
- [ ] Token expires after 24 hours
```

**Action if missing:**
1. Draft suggested content based on code analysis and ticket context
2. Ask user: "PROJ-123 missing WHY/WHAT/HOW/HOW-TO-TEST. Add suggested sections?"
3. If approved → Update ticket with drafted sections
4. Add comment: "Added documentation structure during grooming"

---

### 👤 Assignee

**Check:**
- [ ] Ticket has an assignee
- [ ] Assignee is active team member
- [ ] Assignee has capacity for this work
- [ ] Assignment makes sense (right skills/context)

**Assignment Rules:**
- Unassigned backlog ticket → Assign to current user (default)
- User-specified assignee → Use that instead
- Already assigned → Leave as-is unless reassignment requested

**Actions:**
```typescript
// Get current user
const currentUser = await pm.get_user({ query: "me" })

// Assign ticket
await pm.update_ticket({
  id: ticketId,
  assignee: currentUser.id
})
```

---

### 📊 Status/State

**Check:**
- [ ] Status matches implementation reality
- [ ] Status follows team workflow
- [ ] No "stuck" tickets (In Progress > 2 weeks)
- [ ] No "orphan" tickets (In Review but no PR)

**Status Alignment:**

| Implementation | Correct Status |
|---------------|----------------|
| 0% done, not started | Backlog or Todo |
| 0% done, being worked on | In Progress |
| 1-99% done | Split, then old→Review, new→Todo |
| 100% done | In Review |
| Reviewed and merged | Done |
| Won't implement | Cancelled |

**Actions:**
- Mismatched status → Update to correct status
- Stuck ticket → Comment asking for update, check with assignee
- Orphan ticket → Find PR or revert to In Progress

**Status Change Examples:**
```typescript
// Ticket fully implemented but in "Todo"
await pm.update_ticket({
  id: ticketId,
  state: "In Review"
})

// Add explanatory comment
await pm.add_comment({
  ticket_id: ticketId,
  body: "Implementation complete - all 5 features coded and tested. Moving to Review."
})
```

---

### 🎯 Relevance

**Check:**
- [ ] Feature/fix still needed by business
- [ ] No duplicate tickets
- [ ] Aligns with current product direction
- [ ] Not obsolete due to other changes

**Relevance Questions:**
1. Is this feature still in the roadmap?
2. Has this bug been reported recently?
3. Does this conflict with current architecture?
4. Is there a newer ticket covering this?

**Actions:**
- Still relevant → Continue grooming
- Duplicate → Mark as duplicate (requires confirmation)
- No longer needed → Propose archival (requires confirmation)
- Superseded → Link to new ticket, close old one

**Archival Flow:**
```
1. Identify irrelevant ticket
2. Ask user: "PROJ-123 no longer needed (reason). Archive?"
3. If yes:
   - Add comment explaining why
   - Update state to "Cancelled"
   - Link to replacement ticket if applicable
```

---

### 🧪 Testing/Reproduction

**Check:**
- [ ] Reproduction steps provided (for bugs)
- [ ] Test cases defined (for features)
- [ ] Edge cases identified
- [ ] Known limitations documented

**For Bugs:**
```markdown
## Reproduction
1. Navigate to /checkout
2. Apply discount code "SAVE20"
3. Observe: total doesn't update

Expected: Total reduces by 20%
Actual: Total stays the same

Browser: Chrome 120, Safari 17
Frequency: 100% reproducible
```

**For Features:**
```markdown
## Testing
- [ ] Happy path: User logs in with valid credentials
- [ ] Error path: Invalid credentials show error
- [ ] Edge case: Account locked after 5 failed attempts
- [ ] Edge case: Password reset link expires after 1 hour
```

**Actions:**
- Missing reproduction → Add steps from code analysis
- Missing test cases → Add based on requirements
- Unclear edge cases → Document from technical investigation

---

## Session Checklist

### Before Grooming

- [ ] Identify scope (project/assignee/status filter)
- [ ] Get current user for default assignments
- [ ] Check team's available status states
- [ ] Review team's label conventions

### During Grooming

For each ticket:
1. [ ] Load full ticket details
2. [ ] Run implementation analysis
3. [ ] Complete per-ticket checklist (above)
4. [ ] Take appropriate action (update/split/archive)
5. [ ] Document changes in comments
6. [ ] Move to next ticket

### After Grooming

- [ ] Summary report generated
- [ ] All status changes documented
- [ ] All splits properly linked
- [ ] User confirmations obtained (Review→Done, archival)
- [ ] Next actions identified

---

## Common Grooming Patterns

### Pattern 1: Zombie Tickets (Stale In Progress)

**Detection:**
- Status: "In Progress"
- Last updated: > 14 days ago
- No recent comments

**Actions:**
1. Check codebase for any work
2. If work found → Calculate completion, maybe split
3. If no work found → Move back to "Todo"
4. Comment asking assignee for update

### Pattern 2: Premature Completion

**Detection:**
- Status: "Done"
- Code analysis shows incomplete implementation

**Actions:**
1. Analyze what's missing
2. Reopen ticket → "In Progress"
3. Update description with remaining work
4. Notify assignee

### Pattern 3: Shadow Completion

**Detection:**
- Status: "Backlog" or "Todo"
- Code shows it's fully implemented

**Actions:**
1. Verify implementation is complete
2. Move to "In Review"
3. Comment with evidence (files, functions)
4. Notify assignee to create PR if needed

### Pattern 4: Frankenstein Tickets (Too Many Things)

**Detection:**
- Description has > 10 items
- Items span multiple areas/components
- Some items are quick, some are major

**Actions:**
1. Group related items
2. Split into focused tickets
3. Keep original as parent/epic
4. Link new tickets to parent

### Pattern 5: Vague Tickets

**Detection:**
- Description < 50 characters
- No acceptance criteria
- No technical context
- Uses words like "fix", "improve", "better"

**Actions:**
1. Check related comments/discussions
2. Ask product owner for clarification
3. Update description with context
4. If unclarifiable → Mark for PM review

---

## Grooming Metrics

Track these metrics per session:

- **Tickets groomed:** Total count
- **Statuses corrected:** Count of status changes
- **Splits performed:** Count of ticket splits
- **Archivals proposed:** Count of archival recommendations
- **Labels added:** Count of label corrections
- **Assignees updated:** Count of assignment changes
- **Documentation added:** Count of tickets with WHY/WHAT/HOW/HOW-TO-TEST sections added

**Example Report:**
```
Backlog Grooming Session - 2026-02-14

Scope: Backend Services project, all tickets
Tickets groomed: 23

Actions:
✅ 3 tickets moved to In Review (fully implemented)
✂️ 2 tickets split (partial implementation)
🏷️ 8 tickets labeled (bug/feature)
👤 5 tickets assigned
📚 6 tickets documented (WHY/WHAT/HOW/HOW-TO-TEST added)
🗑️ 1 archival proposed (duplicate)
📝 4 descriptions updated

Backlog health: 87% (20/23 tickets ready to work)
```

---

## Quick Reference

**Full grooming:** Use all checklist items (comprehensive)
**Fast grooming:** Focus on implementation + status + labels (minimal)
**Triage:** Just relevance + priority + assignee (quick pass)

**Typical session time:**
- 5-10 tickets: 15-30 minutes
- 20-30 tickets: 45-60 minutes
- 50+ tickets: Split into multiple sessions

**Frequency:**
- Weekly grooming: Recommended
- Bi-weekly: Acceptable for smaller teams
- Daily: For high-velocity teams
