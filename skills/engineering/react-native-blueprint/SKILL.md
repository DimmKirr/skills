---
name: react-native-blueprint
description: Extract features, API contracts, and design system from React Native / Expo source code. Produces features.md, features.json, and design-system.md for re-implementation. Deterministic detection first, then LLM-enriched analysis.
---

# React Native Blueprint

Extract a complete feature list, API contracts, and design system from a **React Native / Expo** codebase. Deterministic
detection first, then LLM-enriched analysis.

## When to Use

- You have a React Native / Expo codebase to analyze or document
- You need features organized by screen + API capabilities
- You want to extract the design system (colors, typography, spacing, animations)
- You need to understand a "golden UI" app before re-implementing it

## When NOT to use

- Implementing the app (use implement-tdd-autonomously)
- QA/testing an existing app (use frontend-qa or ios-qa)
- Non-React-Native projects (Flutter, SwiftUI, Kotlin)
- Backend or API extraction without a mobile frontend

## Phases

| Phase | Name          | Type                                   | Resource                                                               |
|-------|---------------|----------------------------------------|------------------------------------------------------------------------|
| 0     | Startup       | Taskfile + Playwright debugging        | [resources/phase0-startup.md](resources/phase0-startup.md)             |
| 1     | Detect        | Deterministic inventory                | [resources/phase1-detect.md](resources/phase1-detect.md)               |
| 2     | Screens       | Feature extraction per screen          | [resources/phase2-screens.md](resources/phase2-screens.md)             |
| 3     | API           | Contract mapping                       | [resources/phase3-api.md](resources/phase3-api.md)                     |
| 4     | Output        | Generate features.md + features.json   | [resources/phase4-output.md](resources/phase4-output.md)               |
| 5     | Design System | Visual tokens + Playwright screenshots | [resources/phase5-design-system.md](resources/phase5-design-system.md) |

Phases 0–4 produce the feature inventory. Phase 5 is independently runnable — you can run just Phase 5 if you already
have features.md and only need the design system.

## Progress Checklist

```
React Native Blueprint Progress:
- [ ] Phase 0: App running locally on localhost
- [ ] Phase 1: Screen, API, store, component inventory complete
- [ ] Phase 2: Features extracted per screen
- [ ] Phase 3: API contracts mapped
- [ ] Phase 4: features.md + features.json generated
- [ ] Phase 5: design-system.md generated (optional — run independently)
```

## Scan Scope

**INCLUDE:**

```
app/**/*.tsx                  ← Expo Router screens (primary)
src/components/*.tsx          ← Shared components
src/screens/*.tsx             ← Screen components
src/stores/*.ts               ← State management (Zustand/Redux)
src/services/*.ts             ← API clients
src/hooks/*.ts                ← Custom hooks
src/utils/*.ts, src/types/*.ts, src/constants/*.ts
lib/components/*.tsx, lib/hooks/*.ts
components/*.tsx, hooks/*.ts  ← Root-level shared
styles/*.ts                   ← Stylesheet constants
package.json, app.json, tsconfig.json, .env.example
openapi*.json, swagger*.json  ← API contracts
```

**EXCLUDE:**

```
node_modules/, .expo/, .git/, ios/, android/
fix_*.py, patch_*.js, *_audit.py, master_integration.js
backend_v*/, *_MASTER/
*.log, build_log.txt, diff_index.txt
Files with parentheses/spaces/Python expressions in filename
```

**Golden rule:** If it wouldn't ship in the app bundle, don't scan it.

## How to Execute

1. Read this SKILL.md to orient
2. For each phase you're executing, **read the corresponding resource file first**
3. Follow the resource file instructions precisely
4. Track progress with the checklist above

**For design system only:** Skip to Phase 5 —
read [resources/phase5-design-system.md](resources/phase5-design-system.md) directly. Phase 5 has its own checklist and
is self-contained.
