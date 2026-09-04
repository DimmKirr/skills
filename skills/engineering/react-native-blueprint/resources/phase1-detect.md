# Phase 1: Detect (Deterministic)

Build a complete inventory of the app without LLM interpretation. Run `detect.js` — it scans the codebase and outputs structured JSON. Use that JSON as the context for Phases 2 and 3.

---

## 1.0 Run detect.js First

`detect.js` is a Node.js script that deterministically scans a React Native / Expo codebase and outputs structured JSON. No LLM — pure file system reads, globs, and regex.

**Script location:** `~/.claude/skills/mobile-app-extraction/resources/detect.js`

```bash
node ~/.claude/skills/mobile-app-extraction/resources/detect.js <path-to-app-root>
```

**Output shape:**
```json
{
  "tech": {
    "framework": "react-native",
    "expo_sdk": "~55.0.2",
    "navigation": "expo-router",
    "state": "zustand",
    "api_client": "axios",
    "icon_lib": "@expo/vector-icons",
    "animation_lib": "react-native-reanimated",
    "realtime": false,
    "iap": false,
    "error_tracking": "sentry"
  },
  "screens": [
    { "route": "/(tabs)/feed", "file": "app/(tabs)/feed/index.tsx", "group": "(tabs)", "isTab": true }
  ],
  "api_endpoints": [
    { "method": "GET", "path": "/api/items", "source": "src/services/api.ts" }
  ],
  "stores": [
    { "file": "src/stores/cartStore.ts", "name": "cartStore" }
  ],
  "components": [
    { "file": "src/components/ItemCard.tsx", "name": "ItemCard" }
  ],
  "assets": {
    "images": ["assets/images/logo.png"],
    "icons": [],
    "fonts": ["assets/fonts/Inter.ttf"],
    "total_count": 1
  }
}
```

Save the output:
```bash
node ~/.claude/skills/mobile-app-extraction/resources/detect.js <app-root> > detect-output.json
```

---

## 1.1 Supplement: Framework Details

`detect.js` reads `package.json`. For additional context not covered by the script, also read:

```
app.json → app name, bundle ID, API base URL (if in extra config), plugins, permissions
```

---

## 1.2 Screen Inventory

`detect.js` outputs `screens[]` with `{ route, file, group, isTab }`.

To enrich: identify tab layout from `app/(tabs)/_layout.tsx` — the tab bar icons and labels live there, not in individual screen files.

---

## 1.3 API Contract Discovery

`detect.js` outputs `api_endpoints[]` from service file grep. For fuller coverage:

```
Sources (check in order, merge results):
  1. openapi*.json / swagger*.json → authoritative endpoint list (detect.js flags these)
  2. api_endpoints[] from detect.js → actual client methods
  3. Manual grep in app/ screens for inline fetch calls not caught by the script
```

DO NOT scan: `*.py` files, root-level `*.js` scripts, `backend_v*/` directories.

---

## 1.4 State Store Inventory

`detect.js` outputs `stores[]` with `{ file, name }`.

To enrich: read each store file → identify key state fields and actions. The script gives you the file list; you add semantics.

---

## 1.5 Component Inventory

`detect.js` outputs `components[]` with `{ file, name }`.

To enrich: identify shared (used by 3+ screens) vs feature-specific.

---

## DETECT Output

After running the script and enriching with manual reads, write a summary:

```
App: [name] — React Native [version] / Expo SDK [version]
Navigation: [expo-router / react-navigation]
State: [zustand / redux]

Screens: [N] total
  (tabs): [list]
  (auth): [list]
  (tools): [list]
  (settings): [list]
  (modals): [list]

API Endpoints: [N] total
  Sources: detect.js / OpenAPI / grep

Stores: [N] files → [store names]
Shared Components: [N] files
```

---

## Quality Check

- [ ] `detect.js` ran successfully and output saved
- [ ] Framework version identified (RN + Expo SDK)
- [ ] All screens cataloged (detect.js handles `_layout.tsx` and `+not-found.tsx` exclusion)
- [ ] API endpoints collected from at least 2 sources (detect.js + one more)
- [ ] All store files identified; key state/actions read manually
- [ ] DETECT output summary written before proceeding to Phase 2
