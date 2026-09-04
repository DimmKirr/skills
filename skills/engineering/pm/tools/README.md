# Tool Binding: Abstract Operations

This skill uses abstract ticketing operations that must be mapped to your project management tool's API. See the tool-specific binding file (e.g., [linear.md](linear.md)) for concrete implementations.

## Abstract Operations

### Ticket Operations

| Operation | Purpose | Required Parameters | Returns |
|-----------|---------|-------------------|---------|
| `pm.get_ticket` | Get full ticket details | `id` | Ticket object |
| `pm.list_tickets` | Query tickets with filters | `assignee?`, `state?`, `project?`, `team?`, `label?` | Array of ticket objects |
| `pm.update_ticket` | Modify ticket properties | `id`, plus fields to change | Updated ticket |
| `pm.create_ticket` | Create new ticket | `title`, `team`, `description?`, `assignee?`, `labels?`, `project?` | New ticket object |
| `pm.add_comment` | Add comment to ticket | `ticket_id`, `body` | Comment object |

### User Operations

| Operation | Purpose | Required Parameters | Returns |
|-----------|---------|-------------------|---------|
| `pm.get_user` | Get user info | `query` (ID, email, or "me") | User object |

### Metadata Operations

| Operation | Purpose | Required Parameters | Returns |
|-----------|---------|-------------------|---------|
| `pm.list_statuses` | List workflow states for a team | `team` | Array of status objects |
| `pm.list_labels` | List available labels | `team?` | Array of label objects |

## Ticket Object Shape

The skill expects ticket objects with at least these fields:

```
ticket.id          — unique identifier (for API calls)
ticket.identifier  — human-readable ID (e.g., "PROJ-123")
ticket.title       — ticket title
ticket.description — ticket body (markdown)
ticket.state       — current status name (e.g., "In Review")
ticket.assignee    — assigned user object (or null)
ticket.labels      — array of label objects
ticket.project     — project object (or null)
ticket.team        — team object
ticket.url         — full URL to ticket in the tool's UI
```

## Status Names

The skill uses these status names. Map them to your tool's equivalents:

| Abstract Status | Meaning |
|----------------|---------|
| `Backlog` | Not started, unplanned |
| `Todo` | Planned for current iteration |
| `In Progress` | Active work |
| `In Review` | Code complete, awaiting review |
| `Done` | Completed and reviewed |
| `Cancelled` | Won't implement |

## Sizing / Estimate Values

| Value | Size | Meaning |
|-------|------|---------|
| `1` | S (Small) | Low LLM risk, 1-2 hours |
| `2` | M (Medium) | Moderate LLM risk, 2-8 hours |
| `3` | L (Large) | Higher LLM risk, 1-3 days |
| `4` | XL (Extra Large) | HIGH LLM risk, 3+ days, should be split |

## Available Bindings

- [linear.md](linear.md) -- Linear (MCP: `mcp__linear__*`)
- [jira.md](jira.md) -- Jira (MCP: `mcp__atlassian__*`) -- stub

## Adding a New Tool Binding

To support a new project management tool:

1. Create `tools/{tool}.md` in this directory
2. Map each abstract operation to the tool's MCP calls or API
3. Document any tool-specific quirks (status name differences, field mapping)
4. Verify the ticket object shape is available (or document how to derive it)
