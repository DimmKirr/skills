# Grooming Phases: Detailed Workflow

## Phase 1: Ticket Discovery & Context

1. **Identify Target Tickets**
   - Get tickets for specified project/assignee/status
   - If no filter provided, use current user's assigned tickets
   - **Default scope: Backlog, Todo, and In Progress states**
   - User may explicitly request re-grooming of In Review or other states
   - Unless asked otherwise, tickets already In Review or Done are not re-evaluated

2. **Load Ticket Details**
   - Read full ticket using `pm.get_ticket`
   - Extract: title, description, labels, assignee, status, project
   - Note any existing comments, attachments, relations

## Phase 2: Relevance Analysis

For each ticket, assess:

3. **Current Relevance Check**
   - **Business relevance**: Is this feature/fix still needed?
   - **Product alignment**: Does this match current product direction?
   - **Priority assessment**: Is urgency still accurate?

   **If NOT relevant -> Recommend archival (requires user confirmation)**
   - Reason: "Business priorities changed" or "Feature no longer needed"
   - Action: Propose status -> "Won't Implement" (wait for confirmation)

4. **Status Accuracy Check**
   - Is ticket in the correct status for its actual state?
   - Common mismatches:
     - Ticket in "Todo" but code shows it's implemented -> should be "In Review"
     - Ticket in "In Progress" but no recent activity -> may be "Blocked" or "Backlog"

   **Stale "In Progress" Detection:**
   - Tickets in "In Progress" for **>14 days** without corresponding recent commits are stale
   - Check git log for relevant commits in the date range
   - If code IS fully implemented but status wasn't updated -> move to "In Review" with comment noting the staleness
   - If code is NOT implemented and no recent activity -> move back to "Todo" or "Backlog"
   - Always note the duration in the status change comment (e.g., "In Progress for 35 days with no activity")

   **Auto-fix status** (no confirmation needed except Review -> Done):
   - Update status using `pm.update_ticket`
   - Add comment explaining the status change

## Phase 3: Ticket Sizing

5. **Assess Complexity & LLM Implementation Risk**

   **Sizing Criteria (Primary: LLM Risk)**

   Evaluate each ticket based on:
   1. **LLM Implementation Risk** (primary factor)
      - How many moving pieces? (files, systems, integrations)
      - Will LLM struggle with context/coordination?
      - Multiple subsystems requiring orchestration?
      - Complex state management across components?

   2. **Complexity**
      - Technical difficulty
      - Business logic complexity
      - Integration points

   3. **Time Estimate**
      - Expected implementation time
      - Testing requirements

   **Size Definitions:**

   **1 (S - Small)** - Low LLM risk, 1-2 hours
   - Single file or closely related files
   - Straightforward logic LLM can handle easily
   - Minimal context switching
   - Examples:
     - Fix typo in error message
     - Update configuration value
     - Add single validation rule
     - Simple bug fix in one function

   **2 (M - Medium)** - Moderate LLM risk, 2-8 hours
   - 2-5 files, related functionality
   - LLM can track context across files
   - Some coordination needed but manageable
   - Examples:
     - Add new API endpoint with validation
     - Implement password reset flow
     - Add rate limiting middleware
     - Simple UI form with backend

   **3 (L - Large)** - Higher LLM risk, 1-3 days
   - 5-10 files, multiple components
   - LLM needs careful orchestration
   - Multiple subsystems but related domain
   - Significant testing required
   - Examples:
     - Build user dashboard with charts
     - Implement OAuth2 single provider
     - Payment integration (one gateway)
     - Complex multi-step form with validation

   **4 (XL - Extra Large)** - HIGH LLM risk, 3+ days
   - 10+ files, multiple unrelated subsystems
   - LLM will struggle with context/coordination
   - Requires breaking into smaller, focused pieces
   - Multiple domains that should be separate tickets
   - Examples:
     - Full authentication system (backend + web + mobile)
     - Real-time notifications (WebSocket + mobile + admin)
     - Complete checkout flow (cart + payment + inventory + email)
     - Multi-provider OAuth2 implementation

   **XL Tickets -> Auto-Split**

   When ticket is sized XL (4):
   - **Action:** Automatically decompose into smaller tickets
   - **Strategy:** Break by subsystem, feature area, or technical layer
   - **Goal:** Each new ticket should be M or L (estimate 2-3)
   - **Preserve:** Original ticket becomes parent/epic

   **Apply Sizing:**
   ```typescript
   await pm.update_ticket({
     id: ticketId,
     estimate: 2  // 1=S, 2=M, 3=L, 4=XL
   })
   ```

## Phase 4: Codebase Implementation Analysis

**Evaluation order:** WHY satisfaction first, checklist matching second.

A ticket is done when its business concern (WHY) is resolved, regardless of whether the specific WHAT/HOW checklist items were completed as described. The implementation may have diverged (different approach, done as part of other work, restructured), but if the WHY is satisfied, the ticket is satisfied.

6. **WHY Satisfaction Analysis** (runs FIRST, before checklist matching)

   **Step 1: Extract the business concern**
   - Read the ticket's WHY section (or infer from title/description if no WHY section)
   - Distill to a testable assertion: what user-visible behavior or system property must be true?

   **Step 2: Is this verifiable?**
   - Can you test the behavior? (run a command, check output, read a config, run a test suite)
   - Can you observe the state? (file exists, endpoint responds, UI renders correctly)
   - If NOT verifiable from the codebase/CLI -> skip to step 7 (literal checklist matching)

   **Step 3: Verify the WHY**
   - Run the verification: execute test, check behavior, read output
   - This is behavioral verification, not code matching
   - Example: WHY = "test payment flows without hitting production"
     -> Verification: Can `npm test -- --grep payment` run without network calls?
     -> Result: YES, a mock service intercepts all payment API operations

   **Step 4: If WHY is satisfied -> attribute and recommend**
   - Identify which file/function resolved it (Grep/Glob/Read)
   - Note the divergence: "Ticket describes [approach A], codebase uses [approach B]"
   - **State confidence level explicitly** (e.g., "90% confident", "70% confident") with reasoning:
     - 90%+: Code clearly resolves the business concern, verifiable
     - 70-89%: Code likely resolves it but approach differs significantly or partial verification
     - <70%: Unclear, present finding but recommend keeping open
   - Recommend to user (requires confirmation):
     ```
     WHY satisfied by alternative implementation. (Confidence: 90%)

     Ticket: "Build payment mock server for testing"
     Reality: MockPaymentService in src/services/payment/mock.ts
              intercepts all payment operations. No HTTP mock needed.

     Options:
     a) Move to In Review (WHY is satisfied, approach differs)
     b) Keep open (specific approach still wanted for other reasons)
     c) Rewrite WHAT/HOW to describe remaining delta
     ```
   - **ALWAYS requires user confirmation**: this is a business judgment

   **Step 5: If WHY is NOT satisfied -> fall through to checklist matching**
   - Related code may exist but doesn't resolve the business concern
   - Proceed to step 7 for literal checklist analysis

   **Examples:**

   | Ticket WHY | Verification | Result | Action |
   |------------|-------------|--------|--------|
   | "Test without hitting production API" | Run test suite: do tests make network calls? | No, mock service intercepts them | WHY satisfied, recommend close |
   | "Text on layer ABC must move left 10px" | Check rendered output | Layer ABC merged into XYZ, text already repositioned | WHY satisfied, recommend close |
   | "Users need to see all token balances" | Run `status` command | Only shows USDC + ETH | WHY NOT satisfied, fall through |
   | "Reduce API latency below 200ms" | Need benchmarks, can't verify in grooming | N/A | Skip, fall through to checklist |

7. **Literal Checklist Matching** (fallback when WHY analysis doesn't resolve)

   **Cross-Team Code Location:**
   - Code may live in a different app directory than the team name suggests
   - Always check the root `CLAUDE.md` for team-to-directory mappings before searching
   - When grooming multiple teams, leverage implementation findings from earlier teams to avoid redundant searches

   **Search Strategy:**
   - Use Grep to find related code: search for function names, feature keywords, file paths mentioned in ticket
   - Use Glob to find relevant files: `**/*{feature-name}*`, related test files
   - Read implementation files to understand current state

   **Compute Implementation Status:**
   - Parse ticket description for requirements (look for bullet lists, numbered items, checklists)
   - Match each requirement against codebase findings
   - Calculate completion: `items_done / total_items * 100`

8. **Document Findings**

   Create implementation summary:
   ```
   Implementation Status: X% complete

   Completed (in codebase):
   - [Item 1 from ticket]
   - [Item 2 from ticket]

   Not Yet Implemented:
   - [Item 3 from ticket]
   - [Item 4 from ticket]

   Testing:
   - Reproduction case: [how to test this]
   - Files to check: [relevant file paths]
   ```

   **CRITICAL: Update Stale Paths & Names**

   Ticket descriptions often contain outdated file paths, function names, or technical references. **ALWAYS update them** to match current codebase:

   **Step 1: Extract paths/names from ticket description**
   - Look for file paths (e.g., "src/auth/login.js", "lib/utils.ts")
   - Look for function/class names (e.g., "validateUser()", "AuthService")
   - Look for technical references (e.g., "Redis cache", "PostgreSQL")

   **Step 2: Verify they exist in current codebase**
   ```typescript
   // Use Glob to check if paths still exist
   const mentioned_files = ["src/auth/login.js", "src/services/session.ts"]
   for (const path of mentioned_files) {
     // Check if file exists at this path
     // If not found, search for similar files (may have been moved/renamed)
   }
   ```

   **Step 3: Update description with current paths**

   **Before (stale):**
   ```
   Implement OAuth2
   - Existing auth: src/auth.js
   - Uses login() function
   - Redis for sessions
   ```

   **After (current):**
   ```
   Implement OAuth2

   ## Current Codebase (2026-02-14)
   - Auth service: src/services/auth/index.ts (migrated from src/auth.js)
   - Uses authenticateUser() (renamed from login())
   - Session store: src/lib/redis-session.ts (was inline in src/auth.js)
   ```

   **Step 4: Add "Current Implementation" section**

   Always append current analysis to ticket description:
   ```typescript
   const updatedDescription = `${originalDescription}

   ## Current Implementation (${new Date().toISOString().split('T')[0]})
   **Analyzed during backlog grooming**

   - Auth module: src/services/auth/ (migrated)
   - Token validation: src/middleware/auth.ts
   - Session management: src/lib/session.ts
   - Tests: tests/auth/*.spec.ts
   ```

   **Step 5: When splitting tickets**
   - New ticket: Use CURRENT paths from analysis
   - Original ticket: Update to CURRENT paths for completed work
   - NEVER: Copy old paths without verification

   **Update via ticketing tool:**
   ```typescript
   await pm.update_ticket({
     id: ticketId,
     description: updatedDescription  // With current paths
   })
   ```

## Phase 5: Decision & Action

9. **Handle Based on Completion Status**

   **Case A: WHY Satisfied (alternative implementation)**
   - **Action**: Present finding to user with options (REQUIRES confirmation)
   - **Comment**: Add comment explaining the alternative implementation found
   - **Options presented to user**:
     a) Move to In Review (WHY is satisfied, approach differs but goal met)
     b) Keep open (specific approach still wanted for other reasons)
     c) Rewrite WHAT/HOW to describe remaining delta on top of existing implementation
   - **Wait for user response before taking action**

   **Case B: 100% Implemented (checklist match)**
   - **Action**: Move to "In Review" status (auto, no confirmation)
   - **Tool**: `pm.update_ticket` with `state: "In Review"`
   - **Comment**: Add comment with implementation summary
   - **Notify user**: "Ticket PROJ-123 moved to In Review (fully implemented)"

   **CRITICAL: NEVER MOVE TO "DONE"**
   - **STOP HERE** - Do not move beyond "In Review" automatically
   - Moving from "In Review" to "Done" **REQUIRES USER CONFIRMATION**
   - Add to "Requires Confirmation" section in summary report
   - Wait for user to explicitly approve marking as "Done"

   **Case C: 0% Implemented**
   - **Action**: Verify status is correct (should be "Backlog" or "Todo")
   - **Check labels**: Ensure "bug" or "feature" label exists
   - **Check assignee**: Assign to current user if unassigned
   - **Notify user**: "Ticket PROJ-123 ready to start (0% done)"

   **Case D: Partially Implemented (1-99%)**
   - **Action**: Propose split (execute automatically)
   - **See**: [splitting-workflow.md](splitting-workflow.md) for detailed splitting process

10. **Label Management**

   **Ensure proper labels:**
   - Check if ticket has "bug" or "feature" label
   - **If missing**, analyze ticket title/description:
     - Contains "bug", "fix", "error", "broken" -> label as "bug"
     - Contains "feature", "add", "implement", "new" -> label as "feature"
     - Unclear -> ask user: "Should PROJ-123 be labeled as bug or feature?"

   **Tool**: Use `pm.update_ticket` with labels array

11. **Assignee Management**

   **Default assignment:**
   - If ticket has no assignee -> assign to current user
   - Get current user: `pm.get_user` with `query: "me"`
   - **Tool**: Use `pm.update_ticket` with `assignee: user_id`

   **Override**: User can specify different assignee in grooming command

12. **Description Quality Check (WHY/WHAT/HOW/HOW-TO-TEST)**

    **ALWAYS check if ticket has clear sections:**

    **Required sections:**
    - **WHY**: Business context, problem statement, user impact
    - **WHAT**: What needs to be built/fixed (requirements)
    - **HOW**: Technical approach, implementation details
    - **HOW-TO-TEST**: Acceptance criteria, test scenarios. **TDD link:** When a ticket has a HOW-TO-TEST section, implementers should use the `superpowers:test-driven-development` skill: write tests from the acceptance criteria FIRST, then implement until tests pass.

    **Detection criteria:**

    **Incomplete ticket (missing structure):**
    ```markdown
    # Add user authentication

    We need login functionality.
    ```

    **Complete ticket (has structure):**
    ```markdown
    # Add user authentication

    ## WHY
    Users need secure access to their accounts. Currently, we have no authentication,
    which prevents us from personalizing content and protecting user data.

    ## WHAT
    - [ ] Email/password login
    - [ ] JWT token generation
    - [ ] Protected routes

    ## HOW
    - Use bcrypt for password hashing
    - JWT tokens expire after 24h
    - Middleware: src/middleware/auth.ts
    - Store sessions in Redis

    ## HOW-TO-TEST
    - [ ] User can register with email/password
    - [ ] User can login and receive JWT token
    - [ ] Protected routes return 401 without valid token
    - [ ] Token expires after 24 hours
    ```

    **Action when sections are missing:**

    1. **Analyze the ticket** to understand the context
    2. **Draft suggested content** for missing sections based on:
       - Code analysis (if partially implemented)
       - Ticket title and existing description
       - Related files and comments
    3. **Ask user for approval** using `AskUserQuestion`
    4. **If approved**, update ticket description with suggested WHY/WHAT/HOW/HOW-TO-TEST sections and add a comment noting the addition.

    **Important notes:**
    - This check runs for EVERY ticket during grooming
    - ALWAYS suggest content (don't just point out it's missing)
    - Base suggestions on code analysis and ticket context
    - If ticket already has these sections (even informally), skip
    - Convert existing emojis to markdown checkboxes in WHAT and HOW-TO-TEST
