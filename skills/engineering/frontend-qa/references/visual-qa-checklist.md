# Visual QA Checklist — Tab-by-Tab Template

## Tab Order

Before starting, identify the app's tab structure from the navigation layout file (e.g. `app/(tabs)/_layout.tsx`). List all tabs with their routes.

Example format:
1. Home (`/home`) — Primary content view
2. Browse (`/browse`) — Content discovery
3. Activity (`/activity`) — User activity feed
4. Profile (`/profile`) — User settings and preferences

---

## Per-Tab Checklist Template

For each tab, verify:

**Navigate:** `http://localhost:8081/<tab-route>`

**What to verify:**
- [ ] Correct icon in tab bar (not □ squares)
- [ ] Filter/category pills visible and interactive (if applicable)
- [ ] Content cards render with all expected fields (no `undefined` or missing data)
- [ ] Category/status badges visible and color-coded
- [ ] Numeric values formatted correctly (signs, decimals, units)
- [ ] Status indicators present (pending/active/completed/etc.)
- [ ] Interactive elements respond (buttons, toggles, vote controls)

**Interact:**
- Click each filter option → content should update (or show empty state message)
- Click a card → should navigate to detail screen

**Empty state:** Meaningful message + icon when no data (not blank screen)

---

## Cross-Tab Checks

After visiting all tabs:

- [ ] Tab bar visible on every screen (correct count, correct icons, active state highlights correctly)
- [ ] No tab shows a blank white screen
- [ ] Fonts loaded (icons are icons, not squares `□`)
- [ ] Theme consistent across all tabs (no white flash on dark theme)
- [ ] No JavaScript errors in console (`browser_console_messages`)

## Network Verification

```
mcp__playwright__browser_network_requests (includeStatic: false)
```

Check:
- Requests go to the correct API host (not mock server)
- Auth header present (`Authorization: Bearer ...`)
- Correct query params per tab/filter
- No 401/403/500 status codes
