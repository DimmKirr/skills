# Tool Binding: Jira

Jira-specific implementation of the abstract ticketing operations defined in [README.md](README.md).

> **Status:** Stub -- fill in when a Jira MCP server is available.

## Operation Mapping

### pm.get_ticket → `mcp__atlassian__get_issue`

```typescript
// TODO: verify params when Jira MCP is connected
mcp__atlassian__get_issue({
  issueIdOrKey: "PROJ-123"
})
```

### pm.list_tickets → `mcp__atlassian__search_issues` (JQL)

```typescript
mcp__atlassian__search_issues({
  jql: 'assignee = currentUser() AND status = "To Do" ORDER BY updated DESC',
  maxResults: 50
})
```

### pm.update_ticket → `mcp__atlassian__update_issue`

```typescript
mcp__atlassian__update_issue({
  issueIdOrKey: "PROJ-123",
  fields: {
    status: { name: "In Review" },
    assignee: { accountId: "user-id" },
    labels: ["bug", "p1"]
  }
})
```

### pm.create_ticket → `mcp__atlassian__create_issue`

```typescript
mcp__atlassian__create_issue({
  fields: {
    project: { key: "PROJ" },
    summary: "New ticket title",
    description: "Markdown content",
    issuetype: { name: "Task" },
    assignee: { accountId: "user-id" },
    labels: ["feature"]
  }
})
```

### pm.add_comment → `mcp__atlassian__add_comment`

```typescript
mcp__atlassian__add_comment({
  issueIdOrKey: "PROJ-123",
  body: "Comment in markdown"
})
```

### pm.get_user → `mcp__atlassian__get_current_user`

```typescript
mcp__atlassian__get_current_user()
```

### pm.list_statuses → `mcp__atlassian__get_statuses`

```typescript
// TODO: verify -- Jira statuses are per project/issue-type
mcp__atlassian__get_statuses({
  projectKey: "PROJ"
})
```

### pm.list_labels → `mcp__atlassian__get_labels`

```typescript
// TODO: Jira labels are global, not per-team
mcp__atlassian__get_labels()
```

## Jira-Specific Notes

### Status Mapping

Jira uses configurable workflow states. Common defaults:

| Abstract Status | Jira Default |
|----------------|-------------|
| `Backlog` | `Backlog` |
| `Todo` | `To Do` / `Selected for Development` |
| `In Progress` | `In Progress` |
| `In Review` | `In Review` (may not exist -- check workflow) |
| `Done` | `Done` |
| `Cancelled` | `Cancelled` / `Won't Do` |

### Ticket URLs

Jira URLs follow: `https://{instance}.atlassian.net/browse/PROJ-123`

### Ticket Object Shape Mapping

| Abstract Field | Jira Field |
|---------------|-----------|
| `ticket.id` | `issue.id` |
| `ticket.identifier` | `issue.key` (e.g., "PROJ-123") |
| `ticket.title` | `issue.fields.summary` |
| `ticket.description` | `issue.fields.description` |
| `ticket.state` | `issue.fields.status.name` |
| `ticket.assignee` | `issue.fields.assignee` |
| `ticket.labels` | `issue.fields.labels` (string array, not objects) |
| `ticket.project` | `issue.fields.project` |
| `ticket.team` | N/A (use project or component) |
| `ticket.url` | `issue.self` or construct from instance URL |

### Sizing / Estimate

Jira uses story points (`issue.fields.story_points`) or time estimates. Map the 1-4 scale to your team's convention.
