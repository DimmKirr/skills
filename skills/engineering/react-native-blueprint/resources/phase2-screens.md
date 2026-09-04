# Phase 2: Extract by Screens (LLM-Assisted)

For each screen, read the source file and extract features. Uses the screen_inventory from Phase 1 as input.

---

## Process

```
For each screen in screen_inventory:
  1. Read the screen .tsx file (ONLY files matching INCLUDE scope)
  2. Identify imported components, stores, API calls
  3. Extract features:
     - What data is displayed to the user?
     - What user actions are available? (buttons, forms, gestures, navigation)
     - What business logic is embedded? (calculations, transformations)
     - What state is read/written? (which stores)
     - What API calls are triggered? (which endpoints)
  4. Classify each feature:
     - data_display: showing information to user
     - user_action: button, form, gesture the user performs
     - navigation: routing to another screen
     - real_time: live updates, websockets, polling
     - computation: client-side calculation or analysis
```

---

## Batching Strategy

For large apps (50+ screens), batch by route group:

1. Tab screens `(tabs)/` — main navigation, highest priority, extract first
2. Auth screens `(auth)/`
3. Tool/utility screens `(tools)/` — group similar tools together
4. Settings screens `(settings)/`
5. Modal/overlay screens `(modals)/`
6. Remaining standalone screens

Each batch: read 5–10 screen files, extract features for all in one pass.

---

## Feature Schema (per screen)

```json
{
  "screen_id": "dashboard",
  "route": "/(tabs)/index",
  "file": "app/(tabs)/index.tsx",
  "name": "Dashboard",
  "group": "tabs",
  "purpose": "Real-time data overview and recommendations",
  "features": [
    {
      "id": "dashboard_item_list",
      "name": "Item List Display",
      "description": "Shows real-time recommendations with tier classification",
      "type": "data_display",
      "api_dependencies": ["GET /api/items"],
      "store_dependencies": ["cartStore"],
      "components": ["ItemCard", "CategoryFilterBar"]
    }
  ]
}
```

**ID convention:** `{screen_id}_{feature_slug}` (e.g., `dashboard_item_list`, `portal_filter_bar`)

---

## Quality Check

- [ ] Every screen in screen_inventory has been processed
- [ ] No orphan screens (screens with zero features)
- [ ] Feature IDs are unique and follow `screen_id_feature_slug` convention
- [ ] API dependencies reference real endpoints from api_inventory
- [ ] Store dependencies reference real stores from store_inventory
- [ ] Feature types consistently classified (data_display / user_action / navigation / real_time / computation)
