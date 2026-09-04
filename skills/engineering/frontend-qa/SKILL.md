---
name: frontend-qa
description: >
  Frontend QA workflow for Expo/React Native web apps. Use when asked to:
  test the app locally, verify all tabs/screens work, check if the OpenAPI
  schema is current, test API endpoints directly with curl/hurl, do visual QA
  with Playwright MCP screenshots, assess overall UI quality, or identify
  missing/broken UI elements. Covers: dev server startup, schema freshness
  check, direct API testing, Playwright MCP screenshot analysis, visual quality
  rubric, and critical-thinking checklist for missing elements.
---

# Frontend QA — Expo/React Native Web

## When NOT to use

- Backend-only API testing without a UI (use standard test suites or data-engineer)
- Native iOS QA (use ios-qa with Simulator + WDA)
- Unit testing individual React components in isolation (use standard jest/vitest)
- Non-web platforms (desktop, CLI, embedded)

## 1. Start the Dev Server

```bash
npx expo start --web --no-dev
```

- `--no-dev` is **required** — Hermes outputs `import.meta`; HMR crashes with the `type="module"` patch applied to html.js
- `task start` may fail if Taskfile evaluates env vars globally — use the command above directly
- App available at **http://localhost:8081**
- Wait for "Web Bundled Xms" in terminal before navigating

## 2. Verify OpenAPI Schema is Up-to-Date

See **[api-verification.md](references/api-verification.md#schema-freshness)** for full steps.

Quick check — fetch a live endpoint and diff field names against `openapi.json`:

```bash
curl -s "$API_BASE/api/v1/<resource>?<params>" \
  -H "Authorization: Bearer $TOKEN" | jq '[.items[0] | keys]'
```

If live response fields don't match `openapi.json` → schema is stale → regenerate:

```bash
npx openapi-typescript openapi.json -o src/api/schema.ts
```

Common breakage pattern: API renames a field but `openapi.json` and `schema.ts` are not regenerated — UI silently shows `undefined`.

## 3. Direct API Test

See **[api-verification.md](references/api-verification.md#direct-api-testing)** for auth flow + endpoint patterns.

Goal: confirm the app fetches real data (not stale mock/cached data) and that the shape matches what the UI renders.

### Rule: if the repo has hurl files, use them — do not write ad-hoc curl

If the project's integration test directory contains `*.hurl` files (e.g. `apps/core/integration/**/*.hurl`), those files are the **canonical contract** for every endpoint. They are the response-shape source of truth, the auth-flow source of truth, and the assertion source of truth.

**Always follow this order:**

1. **Run the existing hurl file directly** when probing an endpoint. It already includes auth, captures, and the right field names:
   ```bash
   hurl --variables-file apps/core/integration/vars.dev \
        --variables-file /tmp/cached_jwt \
        apps/core/integration/<area>/<endpoint>.hurl
   ```

2. **If you must use curl + jq** (one-off interactive exploration only), grep the matching hurl file FIRST and copy the canonical field names verbatim:
   ```bash
   # Find the contract file for the endpoint:
   find apps/core/integration -name "*.hurl" | xargs grep -l "<endpoint-path>"

   # Read its [Asserts] block — these ARE the field names you may use in jq:
   grep "jsonpath" apps/core/integration/<area>/<file>.hurl
   ```

3. **Never guess jq keys from the URL path.** A URL `/resources/{id}/items` does NOT mean the response field is `.items`. Always read the contract (hurl file or route handler) first.

4. **If no hurl file exists for the endpoint**, that's a coverage gap worth flagging. Read the route handler's `response_model` class to learn the field names. Still don't guess.

5. **Auth — use the cached-JWT pattern.** The hurl files use an `_auth-once.hurl` to mint a JWT once and cache it. Your curl probes should reuse that cache:
   ```bash
   hurl --variables-file apps/core/integration/vars.dev \
        --json apps/core/integration/_auth-once.hurl \
     | jq -r '.entries[-1].captures[] | "\(.name)=\(.value)"' > /tmp/cached_jwt
   TOKEN=$(grep -oP 'token=\K.*' /tmp/cached_jwt)
   ```

```bash
# Then probe with field names copied from the matching hurl file:
curl -s "$API_BASE/api/v1/<resource>?<params>" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[0]'
```

Compare actual response shape vs what components destructure. If a component reads `item.time` but API returns `item.start_time` → fix the component or regenerate schema.

## 4. Visual QA with Playwright MCP

Use the **Playwright MCP tools** (not Python scripts — MCP is interactive and faster):

```
For each tab/screen:
1. mcp__playwright__browser_navigate  → http://localhost:8081/<tab-route>
2. mcp__playwright__browser_snapshot  → inspect DOM, get element refs
3. mcp__playwright__browser_take_screenshot (filename="tab-name.png") → visual capture
4. Analyze screenshot image directly for visual correctness
5. mcp__playwright__browser_click (ref=...) → interact (expand cards, change filters)
6. mcp__playwright__browser_take_screenshot → capture post-interaction state
```

**Key patterns:**
- Always `browser_snapshot` first to get refs for `browser_click`
- After navigation, use `browser_wait_for` with expected text before snapshotting
- Use `filename` param on screenshots so images persist for comparison
- After filter change, use `browser_network_requests` to confirm correct query params fired

See **[visual-qa-checklist.md](references/visual-qa-checklist.md)** for tab-by-tab checklist template.

## 5. Visual Quality Assessment

When reviewing screenshots, assess against these dimensions:

| Dimension | What to Check |
|-----------|---------------|
| **Typography** | Hierarchy clear? Labels vs data values distinguishable? No truncation? |
| **Color** | Theme consistent? Status colors meaningful and distinguishable? |
| **Spacing** | Cards breathe? No cramped padding? Consistent margins? |
| **Icons** | Actual icons or Unicode squares/emoji boxes? (Font loading issue if squares) |
| **Data format** | Numbers, percentages, currencies formatted consistently? Signs correct? |
| **Empty states** | Meaningful message + icon when no data? Not a blank screen? |
| **Badges/labels** | Status badges visible and color-coded? Category badges distinguishable? |

Identify the app's design language from the codebase (theme config, color constants, design tokens) before starting the visual pass.

## 6. Critical Thinking — What Might Be Missing

After the visual pass, run this checklist:

- **Icons showing as squares?** → `@expo/vector-icons` font not loaded. Fix: `useFonts({ ...Ionicons.font })` in root layout + block render until loaded
- **Signed value bugs?** → Does `-9.7%` show as `+-9.7%`? Format functions that unconditionally prepend `+` break on negatives
- **Filter/category differentiation?** → Without category badge + colored border, all cards look identical (user can't tell categories apart)
- **Date display on cards?** → Upcoming items should show full date+time. Past items should show date in footer
- **Filter params actually sent?** → Open network tab or `browser_network_requests`. Each filter should fire the correct query param
- **Local vs deployed mismatch?** → Deployed site showing stale data → stale deploy, not a code bug
- **Backend vs frontend bug?** → If all categories return identical data → backend issue. File a ticket with reproduction steps. Do NOT paper over it in the UI
- **Accessibility labels accurate?** → `browser_snapshot` shows aria labels. Check they match the visual content
- **Tab count** → Count tabs in tab bar vs expected navigation spec
- **Navigation** → Tapping a card should push a detail screen; back button should return
- **Mock data leak?** → If `EXPO_PUBLIC_MOCK=true`, MSW intercepts requests. Check `.env` to confirm running against live API

## 7. Post-Deploy QA

Run this after every deploy to catch issues that only appear in production (CDN caching, static asset paths, service worker behavior).

**Step 1 — Confirm with user that deploy is live:**
> "Has the deploy finished? What's the URL?"

Do not assume the deploy is complete. Hosting deploys can take 1–3 minutes; a stale version may still be served.

**Step 2 — Navigate to the deployed URL:**

```
mcp__playwright__browser_navigate → <deployed-url>
```

Wait for the app to fully load (auth screen or tab bar visible).

**Step 3 — Run the same visual QA as local (sections 4–6):**

Go through each tab using Playwright MCP screenshots, same checklist from [visual-qa-checklist.md](references/visual-qa-checklist.md).

**Known deploy-only failure modes to check specifically:**

| Issue | Symptom | Cause |
|-------|---------|-------|
| Icons as squares | Tab bar shows □ instead of icons | Icon font not cached / CDN path wrong |
| Stale data | Tab shows outdated content | Stale deploy — old JS bundle served |
| Blank white flash | Screen flickers white before loading | Splash screen not hidden, or SplashScreen.hideAsync() not called |
| Service worker stale | App shows old version after deploy | SW cached old bundle — hard refresh or sw.js cache-bust needed |
| Auth redirect loop | Keeps bouncing to login | Token not persisted in deployed env, or auth hydration failing silently |

**Step 4 — Compare local vs deployed:**

If something works locally but breaks on deployed:
- Check browser DevTools Network tab for 404s on assets
- Check Console for JS errors (`browser_console_messages`)
- Confirm hosting rewrites are correct (SPA needs `"destination": "/index.html"`)
- Check if `public/` contains the latest export (`npx expo export --platform web`)

## Self-Assessment Checklist

Before presenting output to the user, verify:

- [ ] Every tab/screen has at least one screenshot
- [ ] Screenshots evaluated against design system dimensions
- [ ] API response shape matches what UI destructures
- [ ] No console errors in browser logs

## Examples

**User:** "Test the app"
**Skill does:** Starts dev server (`npx expo start --web --no-dev`), navigates to each tab with Playwright MCP, takes screenshots, finds tab bar icons rendering as squares (font not loaded), reports fix: add `useFonts({ ...Ionicons.font })` to root layout.

**User:** "Check if the API schema is current"
**Skill does:** Curls a live endpoint, diffs response fields against `openapi.json`, finds `start_time` field renamed to `startTime` in API but stale in schema, regenerates `schema.ts`.

**User:** "QA the deployed site at https://app.example.com"
**Skill does:** Confirms deploy is live, navigates with Playwright MCP, screenshots each tab, compares against local, finds service worker caching old JS bundle, reports cache-bust fix.
