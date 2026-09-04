# Tool Binding: Linear

Linear-specific implementation of the abstract ticketing operations defined in [README.md](README.md).

## Operation Mapping

### pm.get_ticket → `mcp__linear__get_issue`

```typescript
mcp__linear__get_issue({
  id: "issue-uuid",
  includeRelations: true  // optional: include blocking/related/duplicate relations
})
```

**Returns:** Issue object with `id`, `identifier` (e.g., "ENG-123"), `title`, `description`, `state`, `assignee`, `labels`, `project`, `team`, `url`, `branchName`, and optionally `blockedBy`, `blocks`, `relatedTo`, `duplicateOf`.

### pm.list_tickets → `mcp__linear__list_issues`

```typescript
mcp__linear__list_issues({
  assignee: "me",              // User ID, name, email, or "me"
  state: "Backlog",            // State type, name, or ID
  project: "project-name",     // Project name or ID
  team: "team-name",           // Team name or ID
  label: "bug",                // Label name or ID
  priority: 2,                 // 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
  query: "search text",        // Search title or description
  updatedAt: "-P7D",           // Updated after: ISO-8601 duration
  createdAt: "-P30D",          // Created after: ISO-8601 duration
  includeArchived: false,      // Include archived items
  limit: 50,                   // Max results (default 50, max 250)
  orderBy: "updatedAt",        // Sort field
  cursor: "next-page-cursor"   // Pagination cursor
})
```

### pm.update_ticket → `mcp__linear__save_issue`

```typescript
mcp__linear__save_issue({
  id: "issue-uuid",
  state: "In Review",           // Status name or ID
  assignee: "me",               // User ID, name, email, "me", or null
  labels: ["bug", "p1"],        // Label names or IDs
  title: "Updated title",
  description: "Updated content",
  priority: 2,
  estimate: 2,                  // 1=S, 2=M, 3=L, 4=XL
  dueDate: "2026-03-01",
  project: "project-id",
  team: "team-id",
  cycle: "cycle-name",
  blockedBy: ["PROJ-100"],
  blocks: ["PROJ-200"],
  relatedTo: ["PROJ-300"],
  parentId: "parent-uuid"
})
```

### pm.create_ticket → `mcp__linear__save_issue`

```typescript
mcp__linear__save_issue({
  title: "New ticket title",     // Required
  team: "team-id",               // Required
  description: "Markdown content",
  assignee: "me",
  state: "Todo",
  labels: ["feature"],
  priority: 3,
  estimate: 2,
  project: "project-id",
  cycle: "cycle-name",
  parentId: "parent-uuid",
  blockedBy: ["PROJ-100"],
  relatedTo: ["PROJ-200"],
  links: [{ url: "https://...", title: "Spec doc" }]
})
```

### pm.add_comment → `mcp__linear__save_comment`

```typescript
mcp__linear__save_comment({
  issueId: "issue-uuid",        // Required
  body: "Comment in markdown",   // Required
  parentId: "comment-uuid"       // Optional: for threaded replies
})
```

### pm.get_user → `mcp__linear__get_user`

```typescript
mcp__linear__get_user({
  query: "me"  // User ID, name, email, or "me"
})
```

**Returns:** `id`, `name`, `email`, `active`.

### pm.list_statuses → `mcp__linear__list_issue_statuses`

```typescript
mcp__linear__list_issue_statuses({
  team: "Engineering"  // Team name or ID (required)
})
```

**Returns:** Array of `{ id, name, type, color, position }`. Status types: `unstarted`, `started`, `completed`, `canceled`.

### pm.list_labels → `mcp__linear__list_issue_labels`

```typescript
mcp__linear__list_issue_labels({
  team: "Engineering",   // Optional
  name: "bug",           // Optional filter
  limit: 50
})
```

## Linear-Specific Notes

### Status Name Discovery

Different Linear teams may use different status names. Always call `pm.list_statuses` first:

```typescript
const statuses = await mcp__linear__list_issue_statuses({ team: "Engineering" })
const reviewStatus = statuses.find(s =>
  s.type === "started" && s.name.toLowerCase().includes("review")
)
```

### Ticket URLs

Linear ticket objects include a `.url` property with the full URL (e.g., `https://linear.app/workspace/issue/ENG-123`). Always use this for linking.

### Pagination

Default limit is 50, max 250. Use the `cursor` field from results to fetch the next page.

### Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "Team not found" | Invalid team ID/name | Use `list_teams` to get valid IDs |
| "State not found" | Invalid status name | Use `pm.list_statuses` for the team |
| "User not found" | Invalid assignee | Use `pm.get_user` to verify, or use "me" |
| "Label not found" | Invalid label | Use `pm.list_labels` to get valid labels |
| "Insufficient permissions" | API token missing scopes | Check Linear API token settings |

## Best Practices

1. Always call `pm.get_ticket` before updating to ensure fresh data
2. Use `id` (UUID) for API calls, `identifier` (e.g., "ENG-123") for user-facing messages
3. When updating descriptions, preserve important context
4. Use `relatedTo`, `blocks`, `blockedBy` fields for ticket relationships
5. Test status changes on one ticket before batch updates
6. Add descriptive comments on every status change
