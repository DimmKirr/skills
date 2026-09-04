# Phase 6: Ticket Splitting (Partial Implementation)

**Trigger**: When ticket is 1-99% implemented

## Prepare Split

**Analyze ticket structure:**
- Parse description for task lists (e.g., "- [ ] item")
- Identify bullet points, numbered lists, or sections
- Map each item to implementation status (done vs not done)

**Example:**
```
Original Ticket PROJ-123: "Implement user authentication"
Description:
- [x] Add login endpoint
- [x] Add password hashing
- [x] Add JWT token generation
- [x] Add token validation middleware
- [x] Add logout endpoint
- [x] Add session management
- [x] Add remember-me functionality
- [x] Add password reset flow
- [ ] Add OAuth2 support (Google)
- [ ] Add OAuth2 support (GitHub)

Analysis: 8/10 items done (80% complete)
```

## Execute Split (Auto, no confirmation)

**Step 1: Create new ticket for remaining work**

- Extract incomplete items from original ticket
- Build new ticket description with full context
- Include references to original ticket's context

**New Ticket Content:**
```markdown
# OAuth2 Support for Authentication

Created from PROJ-123 (partially implemented)

## Context
[Copy relevant context from original ticket]

## Remaining Work
- [ ] Add OAuth2 support (Google)
- [ ] Add OAuth2 support (GitHub)

## Implementation Notes
[Add codebase analysis findings to help implementer]
- Existing auth code: src/auth/
- Token validation: src/middleware/auth.ts
- Session management: src/services/session.ts
```

**Tool**: Use `pm.create_ticket` with:
- `team`: same as original ticket
- `project`: same as original ticket
- `assignee`: same as original ticket
- `labels`: same as original ticket
- `title`: focused on remaining work
- `description`: new ticket content

**Step 2: Update original ticket**

- Remove incomplete items from description
- Keep only completed items
- Update title if needed (e.g., remove "Implement" if fully done)

**Updated Original Ticket:**
```markdown
# User authentication (core features)

## Completed Implementation
- [x] Add login endpoint
- [x] Add password hashing
- [x] Add JWT token generation
- [x] Add token validation middleware
- [x] Add logout endpoint
- [x] Add session management
- [x] Add remember-me functionality
- [x] Add password reset flow

Split to PROJ-456 for OAuth2 support
```

**Tool**: Use `pm.update_ticket` with updated description

**Step 3: Link tickets with FULL URLs**

**CRITICAL: ALWAYS use FULL ticket URLs, NEVER just ticket IDs**

Get full URLs from the ticket objects returned by the ticketing tool:
```typescript
// After creating new ticket, both tickets have .url property
const originalTicketUrl = originalTicket.url  // e.g., "{ticket.url}"
const newTicketUrl = newTicket.url            // e.g., "{ticket.url}"
```

**Add comments with FULL URLs (required format):**

**Old ticket comment:**
```typescript
await pm.add_comment({
  ticket_id: originalTicket.id,
  body: `Split to ${newTicket.identifier}: ${newTicket.url}`
})
```

**New ticket comment:**
```typescript
await pm.add_comment({
  ticket_id: newTicket.id,
  body: `Created from ${originalTicket.identifier}: ${originalTicket.url}`
})
```

**Format enforcement:**
- Correct: `"Split to PROJ-456: https://pm-tool.example/issue/PROJ-456"`
- Wrong: `"Split to PROJ-456"` (missing URL)
- Wrong: `"Split to https://pm-tool.example/issue/PROJ-456"` (missing ticket ID)
- Always: `{ticket-id}: {full-url}`

## Report Split to User

```
Ticket Split: PROJ-123

Original: "Implement user authentication" (80% done)
-> Kept in PROJ-123: 8 completed items
-> Moved to PROJ-456: 2 remaining items (OAuth2)

Actions taken:
- Created PROJ-456 with same assignee and project
- Updated PROJ-123 description (removed incomplete items)
- Linked tickets with comments
- PROJ-123 status -> In Review (completed portion)

Next: Review PROJ-123, then start PROJ-456
```
