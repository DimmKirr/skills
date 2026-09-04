# Ticket Splitting Examples

Real-world examples of splitting partially implemented tickets.

## Example 1: Feature with Todo List

### Original Ticket: PROJ-123

**Title:** Implement user authentication system

**Description:**
```markdown
# User Authentication System

Build complete authentication for the application.

## Requirements
- [ ] Add login endpoint (POST /auth/login)
- [ ] Add password hashing (bcrypt)
- [ ] Add JWT token generation
- [ ] Add token validation middleware
- [ ] Add logout endpoint (POST /auth/logout)
- [ ] Add session management
- [ ] Add remember-me functionality
- [ ] Add password reset flow
- [ ] Add OAuth2 support (Google)
- [ ] Add OAuth2 support (GitHub)

## Acceptance Criteria
- Users can log in with email/password
- Tokens expire after 24 hours
- Sessions are persisted in Redis
- OAuth2 providers work end-to-end
```

**Status:** In Progress
**Assignee:** @alice
**Labels:** feature, auth
**Project:** Backend Services

### Analysis

**Codebase findings:**
- ✅ Login endpoint exists: `src/routes/auth.ts` (lines 10-45)
- ✅ Password hashing implemented: `src/utils/crypto.ts` (bcrypt setup)
- ✅ JWT generation: `src/services/token.ts`
- ✅ Token middleware: `src/middleware/auth.ts`
- ✅ Logout endpoint: `src/routes/auth.ts` (lines 60-75)
- ✅ Session management: `src/services/session.ts` (Redis integration)
- ✅ Remember-me: `src/middleware/auth.ts` (lines 30-45)
- ✅ Password reset: `src/routes/auth.ts` (lines 80-120), email templates exist
- ❌ OAuth2 (Google): No code found
- ❌ OAuth2 (GitHub): No code found

**Completion:** 8/10 items = 80% complete

### Split Decision

**Keep in PROJ-123:** Core authentication (8 completed items)
**Move to new ticket:** OAuth2 integration (2 remaining items)

### After Split

#### Updated PROJ-123

**Title:** User authentication system (core features)

**Description:**
```markdown
# User Authentication System - Core Features

✅ **Implementation Complete**

## Completed Features
- [x] Login endpoint (POST /auth/login) - `src/routes/auth.ts`
- [x] Password hashing (bcrypt) - `src/utils/crypto.ts`
- [x] JWT token generation - `src/services/token.ts`
- [x] Token validation middleware - `src/middleware/auth.ts`
- [x] Logout endpoint (POST /auth/logout) - `src/routes/auth.ts`
- [x] Session management - `src/services/session.ts`
- [x] Remember-me functionality - `src/middleware/auth.ts`
- [x] Password reset flow - `src/routes/auth.ts`, email templates

## Implementation Details
- Sessions stored in Redis
- Tokens expire after 24 hours
- Password reset sends email via SendGrid
- All endpoints have test coverage

---

**Split to PROJ-456** for OAuth2 provider support
```

**Status:** In Review (moved from In Progress)
**Comment added:** "Split to PROJ-456: https://pm-tool.example/issue/PROJ-456"

#### New Ticket: PROJ-456

**Title:** Add OAuth2 authentication providers (Google, GitHub)

**Description:**
```markdown
# OAuth2 Authentication Support

**Created from PROJ-123** (core auth system complete)

## Context
The base authentication system is fully implemented with email/password login, JWT tokens, session management, and password reset. This ticket adds OAuth2 social login providers.

## Requirements
- [ ] Add OAuth2 support for Google Sign-In
  - Register OAuth2 app in Google Cloud Console
  - Implement /auth/google/callback endpoint
  - Handle token exchange and user creation
  - Test with Google accounts
- [ ] Add OAuth2 support for GitHub
  - Register OAuth App in GitHub settings
  - Implement /auth/github/callback endpoint
  - Handle token exchange and user creation
  - Test with GitHub accounts

## Technical Notes

**Existing auth system:**
- Login endpoint: `src/routes/auth.ts`
- Token generation: `src/services/token.ts`
- User model: `src/models/user.ts`
- Session management: `src/services/session.ts`

**Suggested approach:**
1. Add OAuth2 strategy using Passport.js or similar
2. Store OAuth tokens in user record (add `oauth_provider` and `oauth_id` fields)
3. Reuse existing JWT token generation for consistent sessions
4. Link OAuth accounts to existing users by email if they already exist

**Environment variables needed:**
```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

## Acceptance Criteria
- Users can log in with "Sign in with Google" button
- Users can log in with "Sign in with GitHub" button
- OAuth accounts link to existing users by email
- OAuth login creates JWT token like password login
- Sessions work identically to password-based auth

## Reference
- Original ticket: PROJ-123 (https://pm-tool.example/issue/PROJ-123)
- Auth implementation: `src/routes/auth.ts`, `src/services/token.ts`
```

**Status:** Todo
**Assignee:** @alice (same as original)
**Labels:** feature, auth (same as original)
**Project:** Backend Services (same as original)
**Comment added:** "Created from PROJ-123: https://pm-tool.example/issue/PROJ-123"

---

## Example 2: Bug Fix with Multiple Sub-Issues

### Original Ticket: PROJ-234

**Title:** Fix checkout flow errors

**Description:**
```markdown
# Checkout Flow Issues

Multiple bugs reported in checkout:

1. Cart total calculation incorrect when discount code applied
2. Payment fails silently on expired cards
3. Order confirmation email not sending
4. Inventory not updating after successful purchase
5. Shipping address validation allowing invalid ZIP codes
```

**Status:** In Progress
**Labels:** bug, checkout, p1

### Analysis

**Codebase findings:**
- ✅ Issue #1: Fixed in `src/services/cart.ts` (line 45-60) - discount calculation corrected
- ✅ Issue #2: Fixed in `src/services/payment.ts` (line 120-135) - error handling added
- ✅ Issue #3: Fixed in `src/services/email.ts` (line 80-95) - queue retry logic added
- ❌ Issue #4: Inventory service still doesn't decrement stock
- ❌ Issue #5: ZIP validation still accepts invalid formats

**Completion:** 3/5 issues = 60% complete

### Split Decision

**Keep in PROJ-234:** Fixed issues (cart, payment, email)
**Move to new ticket:** Remaining issues (inventory, shipping)

### After Split

#### Updated PROJ-234

**Title:** Fix checkout flow errors (cart, payment, email)

**Description:**
```markdown
# Checkout Flow - Fixed Issues

✅ **Fixes Complete**

## Resolved Issues

**1. Cart total calculation with discounts** ✅
- Fixed in: `src/services/cart.ts` (lines 45-60)
- Issue: Discount wasn't applied to tax calculation
- Fix: Apply discount before tax calculation

**2. Payment error handling** ✅
- Fixed in: `src/services/payment.ts` (lines 120-135)
- Issue: Expired card failures were silent
- Fix: Added proper error handling and user messaging

**3. Order confirmation emails** ✅
- Fixed in: `src/services/email.ts` (lines 80-95)
- Issue: Emails not sending on queue failures
- Fix: Added retry logic with exponential backoff

## Testing
- Cart: Tested with 10%, 25%, 50% discount codes ✅
- Payment: Tested with expired test cards (Stripe) ✅
- Email: Verified retry queue in Redis ✅

---

**Split to PROJ-567** for inventory and shipping validation
```

**Status:** In Review
**Comment added:** "Split to PROJ-567: https://pm-tool.example/issue/PROJ-567"

#### New Ticket: PROJ-567

**Title:** Fix checkout inventory and shipping validation

**Description:**
```markdown
# Checkout: Inventory & Shipping Fixes

**Created from PROJ-234** (cart/payment/email issues resolved)

## Context
The checkout flow had 5 reported bugs. Three are now fixed (cart calculation, payment errors, confirmation emails). This ticket addresses the remaining two issues.

## Remaining Issues

**4. Inventory not updating after purchase**
- **Problem:** Stock count doesn't decrement when order completes
- **Expected:** After successful payment, product inventory should decrease
- **Current behavior:** Inventory stays the same, leading to overselling
- **Impact:** High - customers ordering out-of-stock items

**5. Shipping address ZIP code validation**
- **Problem:** Invalid ZIP codes accepted (e.g., "00000", "12345-", "ABCDE")
- **Expected:** Validate ZIP format before allowing checkout
- **Current behavior:** Any 5-character string accepted
- **Impact:** Medium - shipping delays and failed deliveries

## Technical Context

**Inventory Service:**
- Current implementation: `src/services/inventory.ts`
- Products table: `products` (has `stock_quantity` column)
- Order processing: `src/services/order.ts` (needs inventory call added)

**Shipping Validation:**
- Current validation: `src/validators/address.ts` (line 25-40)
- Uses simple length check, no format validation
- Should validate: US ZIP (5 digits or 5+4 format), Canadian postal codes

## Suggested Fixes

**Inventory:**
```typescript
// In src/services/order.ts after payment success
await inventoryService.decrementStock(orderItems)
```

**ZIP Validation:**
```typescript
// In src/validators/address.ts
const US_ZIP_REGEX = /^\d{5}(-\d{4})?$/
const CA_POSTAL_REGEX = /^[A-Z]\d[A-Z] \d[A-Z]\d$/
```

## Acceptance Criteria

**Inventory:**
- [ ] Stock decrements after successful payment
- [ ] Out-of-stock products can't be purchased
- [ ] Race conditions handled (two orders for last item)
- [ ] Inventory restored if order cancelled within 30 min

**Shipping:**
- [ ] US ZIP codes validated (12345 or 12345-6789)
- [ ] Canadian postal codes validated (A1A 1A1)
- [ ] Invalid formats show clear error message
- [ ] Validation works on both web and mobile checkout

## Reference
- Original ticket: PROJ-234 (https://pm-tool.example/issue/PROJ-234)
- Inventory service: `src/services/inventory.ts`
- Address validator: `src/validators/address.ts`
```

**Status:** Todo
**Assignee:** (same as original)
**Labels:** bug, checkout, p1 (same as original)
**Comment added:** "Created from PROJ-234: https://pm-tool.example/issue/PROJ-234"

---

## Example 3: Epic/Large Feature (Descriptive Sections)

### Original Ticket: PROJ-345

**Title:** Implement real-time notifications system

**Description:**
```markdown
# Real-Time Notifications System

## Overview
Build push notification system for web and mobile apps.

## Backend Infrastructure
Set up notification service with WebSocket server, message queue (RabbitMQ), and delivery tracking database.

## Web Client
Implement browser notifications using Service Workers, notification permission handling, and WebSocket connection for real-time delivery.

## Mobile Apps
Integrate FCM (Firebase Cloud Messaging) for iOS and Android push notifications.

## Admin Panel
Build admin interface for sending broadcast notifications, scheduling campaigns, and viewing delivery analytics.

## Analytics & Monitoring
Track notification delivery rates, click-through rates, and user engagement metrics.
```

**Status:** In Progress

### Analysis

**Codebase findings:**
- ✅ Backend: WebSocket server exists (`src/ws/server.ts`), RabbitMQ integration done, delivery tracking DB schema created
- ✅ Web Client: Service Worker registered, permission handling implemented, WebSocket client connected
- ❌ Mobile Apps: No FCM integration found
- ❌ Admin Panel: No admin routes or UI found
- ❌ Analytics: No tracking code found

**Completion:** 2/5 sections = 40% complete

### Split Decision

**Keep in PROJ-345:** Backend + Web Client (completed)
**Move to new ticket:** Mobile + Admin + Analytics

### After Split

#### Updated PROJ-345

**Title:** Real-time notifications system (backend + web)

**Description:**
```markdown
# Real-Time Notifications - Backend & Web

✅ **Implementation Complete**

## Completed Components

### Backend Infrastructure ✅
- WebSocket server: `src/ws/server.ts`
- RabbitMQ queue: `src/queues/notifications.ts`
- Delivery tracking: `notifications` and `notification_deliveries` tables
- REST API: `POST /api/notifications` endpoint

### Web Client ✅
- Service Worker: `public/sw.js` (notification handling)
- Permission flow: `src/components/NotificationPrompt.tsx`
- WebSocket client: `src/services/websocket.ts`
- Real-time delivery working in browser

## Technical Details

**WebSocket Server:**
- Port: 8080 (configurable via WS_PORT)
- Authentication via JWT token in connection URL
- Handles: connect, disconnect, notification delivery
- Scales horizontally with Redis pub/sub

**Message Queue:**
- RabbitMQ exchange: `notifications`
- Queue: `notification-delivery`
- Retry logic: 3 attempts with exponential backoff
- Dead letter queue for failed notifications

**Database Schema:**
```sql
notifications (id, user_id, title, body, type, created_at)
notification_deliveries (notification_id, delivered_at, read_at)
```

## Testing
- WebSocket connections: Tested with 1000 concurrent users ✅
- Browser notifications: Tested on Chrome, Firefox, Safari ✅
- Message queue: Load tested with 10k messages/min ✅

---

**Split to PROJ-678** for mobile apps, admin panel, and analytics
```

**Status:** In Review
**Comment added:** "Split to PROJ-678: https://pm-tool.example/issue/PROJ-678"

#### New Ticket: PROJ-678

**Title:** Notifications: Mobile apps, admin panel, and analytics

**Description:**
```markdown
# Notifications - Mobile, Admin & Analytics

**Created from PROJ-345** (backend + web complete)

## Context
The notification system backend and web client are fully implemented and deployed. This ticket completes the system with mobile app support, admin tooling, and analytics tracking.

## Remaining Components

### 1. Mobile Apps - FCM Integration

**iOS:**
- [ ] Add Firebase SDK to iOS app
- [ ] Configure APNs certificates in Firebase Console
- [ ] Implement notification permission request
- [ ] Handle notification tap (deep linking)
- [ ] Test on physical iOS devices

**Android:**
- [ ] Add Firebase SDK to Android app
- [ ] Configure FCM in Firebase Console
- [ ] Implement notification channels (Android 8+)
- [ ] Handle notification tap (deep linking)
- [ ] Test on physical Android devices

**Technical notes:**
- Backend endpoint exists: `POST /api/notifications` accepts FCM tokens
- Store device tokens in `user_devices` table (schema ready)
- Reuse notification types from web: `info`, `warning`, `success`, `message`

### 2. Admin Panel

**Features:**
- [ ] Dashboard showing notification stats (sent, delivered, read)
- [ ] Send broadcast notification form (all users or filtered)
- [ ] Schedule notification campaigns (date/time picker)
- [ ] View notification history with delivery status
- [ ] Filter by user, type, date range

**Suggested tech stack:**
- Add admin routes to existing Next.js app: `/admin/notifications`
- Use existing auth system (require admin role)
- Charts: Recharts or Chart.js
- Table: TanStack Table (already in project)

**API endpoints needed:**
```typescript
GET  /api/admin/notifications/stats
POST /api/admin/notifications/broadcast
GET  /api/admin/notifications/history
POST /api/admin/notifications/schedule
```

### 3. Analytics & Monitoring

**Metrics to track:**
- [ ] Delivery rate (% notifications successfully delivered)
- [ ] Click-through rate (% notifications clicked/opened)
- [ ] Opt-out rate (% users disabling notifications)
- [ ] Time-to-delivery (latency from send to device)
- [ ] Platform breakdown (web vs iOS vs Android)

**Implementation:**
- Add analytics events in Service Worker and mobile apps
- Store metrics in `notification_analytics` table
- Dashboard charts in admin panel
- Alerting for delivery rate < 95%

**Tracking events:**
```typescript
notification.sent
notification.delivered
notification.displayed
notification.clicked
notification.dismissed
```

## Technical Context

**Existing backend:**
- Notification service: `src/services/notification.ts`
- WebSocket server: `src/ws/server.ts`
- Database tables ready: `notifications`, `user_devices`, `notification_analytics`

**Mobile app repos:**
- iOS: `mobile-ios/` (React Native)
- Android: `mobile-android/` (React Native)

## Acceptance Criteria

**Mobile:**
- Users receive push notifications on iOS and Android
- Tapping notification opens relevant screen in app
- Notification settings sync across devices

**Admin:**
- Admins can send broadcast notifications
- Admins can schedule campaigns for future date/time
- Dashboard shows live stats (refreshes every 30s)

**Analytics:**
- Delivery and CTR metrics visible in admin dashboard
- Alerts trigger when delivery rate drops below 95%
- Weekly report email sent to product team

## Reference
- Original ticket: PROJ-345 (https://pm-tool.example/issue/PROJ-345)
- Backend implementation: `src/services/notification.ts`, `src/ws/server.ts`
- Web client: `src/services/websocket.ts`, `public/sw.js`
```

**Status:** Todo
**Assignee:** (same as original)
**Labels:** feature, notifications (same as original)
**Comment added:** "Created from PROJ-345: https://pm-tool.example/issue/PROJ-345"

---

## Key Splitting Principles

### 1. Clear Boundaries
- Split along **completed vs not-started** lines
- Don't split partially-implemented features
- Each ticket should be independently testable

### 2. Context Preservation
- New ticket includes all relevant context from original
- Reference specific files, functions, endpoints
- Include technical notes from code analysis
- Link to original ticket with full URL

### 3. Actionable Tickets
- New ticket is ready to implement (no discovery needed)
- Includes acceptance criteria
- Has clear technical guidance
- Suggests implementation approach

### 4. Maintain Relationships
- Same assignee, project, labels
- Link tickets bidirectionally (comments with full URLs)
- Explain split rationale in both tickets

### 5. Update Descriptions
- Original: Keep only completed items
- Original: Change title to reflect actual scope
- New: Remove completed portions
- New: Focus on remaining work

### 6. Status Management
- Original → "In Review" (if 100% of remaining scope done)
- New → "Todo" (ready to start)
- Both get explanatory comments
