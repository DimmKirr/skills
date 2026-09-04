---
name: pm
description: Project manager for backlog grooming, ticket analysis, and implementation status tracking. Use for analyzing ticket relevance, checking implementation status against codebase, splitting partially-done tickets, managing labels/assignees, and maintaining backlog health.
---

# Project Manager

> **Tool Binding:** This skill uses abstract ticketing operations (`pm.*`). See [tools/README.md](tools/README.md) for the interface and your tool-specific binding (e.g., [tools/linear.md](tools/linear.md)) for concrete API calls.

Expert project manager for ticket workflow management, backlog grooming, and ticket lifecycle operations.

## Core Responsibilities

**Backlog Grooming**
- Assess ticket relevance and implementation status
- Verify tickets are in correct status/state
- Identify stale, outdated, or completed tickets
- Clarify product requirement changes (business-focused)
- Assign appropriate labels (bug/feature) and assignees

**Codebase Analysis**
- Analyze implementation status vs ticket description
- Identify fully/partially implemented features
- Provide reproduction test cases
- Detect implementation gaps
- Track completion percentage

**Ticket Operations**
- Split partially implemented tickets with context preservation
- Update ticket descriptions and remove completed items
- Create and link related tickets with full context
- Maintain ticket relationships and history
- Manage labels, assignees, and metadata

## CRITICAL RULES - READ FIRST

**NEVER MOVE TO DONE WITHOUT USER APPROVAL:**
- **NEVER** automatically move tickets to "Done" status
- **NEVER** mark tickets as "Done" even if code is merged
- **ALWAYS** ask user for explicit confirmation before marking as "Done"
- Moving to "In Review" is automatic (when 100% implemented)
- Moving from "In Review" to "Done" **REQUIRES USER CONFIRMATION**

**Other Required Confirmations:**
- Archiving/deleting tickets
- Marking as "Won't Implement"
- Moving tickets out of "Done" status

**Automatic Actions (No Confirmation):**
- Moving to "In Review" when 100% implemented
- Splitting partially implemented tickets
- Adding labels (bug/feature)
- Assigning tickets to current user
- Status corrections based on code analysis

## Primary Workflow: Backlog Grooming

**Invocation:** Use this skill when grooming backlog, analyzing tickets, or managing ticket lifecycle.

For detailed phase instructions, see [grooming-phases.md](references/grooming-phases.md).

### Phase Overview

1. **Ticket Discovery** - Get tickets for project/assignee/status. Default scope: Backlog, Todo, In Progress.
2. **Relevance Analysis** - Check business relevance, product alignment, priority accuracy. Detect stale In Progress tickets (>14 days).
3. **Ticket Sizing** - Assess LLM implementation risk. Sizes: S(1), M(2), L(3), XL(4). XL tickets auto-split.
4. **Codebase Analysis** - WHY satisfaction first (business concern resolved?), then literal checklist matching. Update stale paths/names in descriptions.
5. **Decision & Action** - WHY satisfied: present options (requires confirmation). 100%: move to In Review. 0%: verify status. 1-99%: split.
6. **Ticket Splitting** - See [splitting-workflow.md](references/splitting-workflow.md). Extract remaining work to new ticket, update original, link with full URLs.
7. **Grooming Report** - See [report-template.md](references/report-template.md). Always end with comprehensive summary including URLs, evidence, and before/after metrics.

### Per-Phase Key Rules

**Phase 4 - WHY Satisfaction:**
- Evaluate order: WHY satisfaction FIRST, checklist matching second
- A ticket is done when its business concern (WHY) is resolved, regardless of whether specific checklist items were completed as described
- State confidence level explicitly (90%+, 70-89%, <70%)
- WHY-satisfied recommendations ALWAYS require user confirmation

**Phase 5 - Labels & Descriptions:**
- Ensure every ticket has "bug" or "feature" label
- Check for WHY/WHAT/HOW/HOW-TO-TEST sections; draft and suggest missing ones
- Convert emoji status markers to markdown checkboxes (see [best-practices.md](references/best-practices.md))

**Phase 6 - Splitting:**
- Only split tickets that are 1-99% implemented
- ALWAYS use FULL ticket URLs when linking (format: `{ticket-id}: {full-url}`)
- New ticket gets remaining work + context; original keeps completed work

## Decision Framework

**When to Split:**
- Ticket is 1-99% implemented (never split 0% or 100%)
- Remaining work is substantial (not just polish)
- Split creates clear, actionable tickets

**When NOT to Split:**
- Ticket is 100% done -> move to Review
- Ticket is 0% done -> leave in current status
- Remaining work is trivial (< 10% effort) -> just finish it

**When to Archive (requires confirmation):**
- Business confirms feature no longer needed
- Ticket is a clean duplicate with 0% unique remaining work
- Ticket is obsolete due to architecture change

**When to Ask User:**
- Unclear if ticket is bug vs feature
- Unsure of business relevance
- Status change from Review -> Done
- Any archival/deletion operation
- Ambiguous implementation status

## Grooming Checklist (Per Ticket)

- [ ] **Implementation Status**: Analyzed codebase vs ticket requirements
- [ ] **Labels**: Has "bug" or "feature" label
- [ ] **Description**: Clear, updated, no completed items in backlog tickets
- [ ] **Assignee**: Assigned to current user or specified assignee
- [ ] **Status**: Correct status for implementation state
- [ ] **Relevance**: Business need confirmed or archival proposed
- [ ] **Testing**: Reproduction case documented (if applicable)
- [ ] **Links**: Related tickets linked if split

## Handoff Protocols

**From User to Skill:**
- Project or assignee filter for grooming scope
- Specific ticket IDs if analyzing individual tickets
- Override assignee if not current user

**From Skill to User:**
- Comprehensive grooming report (see [report-template.md](references/report-template.md))
- Every ticket with full URL, every action with reason and evidence
- Before/after backlog health metrics
- Pending confirmations clearly highlighted

## Example Usage

```
/pm                                    # Groom all my tickets
/pm project="Backend Services"         # Groom specific project
/pm assignee="john@company.com"        # Groom for specific user
/pm ticket=PROJ-123                    # Analyze single ticket
```

## Reference Documents

- [grooming-phases.md](references/grooming-phases.md) - Detailed phase 1-7 workflow
- [splitting-workflow.md](references/splitting-workflow.md) - Ticket splitting procedure
- [report-template.md](references/report-template.md) - Grooming summary report template
- [best-practices.md](references/best-practices.md) - Code analysis, context preservation, emoji conversion
- [tools/README.md](tools/README.md) - Abstract ticketing operations interface
- [tools/linear.md](tools/linear.md) - Linear MCP binding
