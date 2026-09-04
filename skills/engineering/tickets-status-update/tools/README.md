# Tool Binding: Abstract Operations

This skill uses a small subset of the abstract ticketing operations also used by the `/pm` skill. Map them to your project management tool's API.

## Abstract Operations

| Operation | Purpose | Required Parameters | Returns |
|-----------|---------|-------------------|---------|
| `pm.get_ticket` | Resolve ticket, get `identifier` + `url` | `id` | Ticket object |
| `pm.add_comment` | Post the status update comment | `ticket_id`, `body` | Comment object |

The skill expects ticket objects with at least `id`, `identifier` (e.g. "PROJ-123"), `title`, `state`, and `url`.

## Linear (MCP: `mcp__linear__*`)

### pm.get_ticket → `mcp__linear__get_issue`

```typescript
mcp__linear__get_issue({
  id: "PROJ-123"  // identifier or UUID
})
```

**Returns:** issue with `id`, `identifier`, `title`, `state`, `url`.

### pm.add_comment → `mcp__linear__save_comment`

```typescript
mcp__linear__save_comment({
  issueId: "issue-uuid",   // Required
  body: "Comment in markdown"  // Required; use real newlines, not \n escapes
})
```

## Jira (MCP: `mcp__atlassian__*`)

> **Status:** Stub. Verify params when a Jira MCP server is connected.

### pm.get_ticket → `mcp__atlassian__get_issue`

```typescript
mcp__atlassian__get_issue({
  issueIdOrKey: "PROJ-123"
})
```

### pm.add_comment → `mcp__atlassian__add_comment`

```typescript
mcp__atlassian__add_comment({
  issueIdOrKey: "PROJ-123",
  body: "Comment in markdown"
})
```

Jira ticket URLs follow `https://{instance}.atlassian.net/browse/PROJ-123`.

## Adding a New Tool Binding

1. Add a section for the tool in this file (or a `tools/{tool}.md` if it grows large).
2. Map `pm.get_ticket` and `pm.add_comment` to the tool's MCP calls or API.
3. Document how to obtain the ticket's human-readable identifier and full URL.
