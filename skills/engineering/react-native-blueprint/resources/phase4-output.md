# Phase 4: Output

Generate the two output files from Phase 1–3 data: `features.md` (human review) and `features.json` (machine consumption).

---

## features.md Template

```markdown
# [App Name] — Feature List

## App Overview
- **Framework:** React Native [version] / Expo SDK [version]
- **Navigation:** [expo-router / react-navigation]
- **State:** [zustand / redux]
- **Total Screens:** [N]
- **Total API Endpoints:** [N]
- **Total Features:** [N]

---

## Features by Screen

### [Route Group Name] (e.g., Main Tabs)

#### [Screen Name] (`route`)
**Purpose:** [one-line description]

| # | Feature | Type | API Deps | Description |
|---|---------|------|----------|-------------|
| 1 | [name]  | [type] | [endpoints] | [description] |

[Repeat for each screen, grouped by route group]

---

## Features by API Contract

### [Category Name]

#### `METHOD /path` — [description]
- **Params:** [list]
- **Response:** [shape]
- **Consumed by:** [screen list]
- **Features:** [feature list]

[Repeat for each endpoint, grouped by category]

---

## Cross-Reference Matrix

| Screen | Endpoint 1 | Endpoint 2 | ... |
|--------|-----------|-----------|-----|
| Screen A | X | | |
| Screen B | | X | |
```

---

## features.json Template

```json
{
  "app": {
    "name": "",
    "framework": "react-native",
    "expo_sdk": "",
    "version": "",
    "navigation": "",
    "state_management": "",
    "total_screens": 0,
    "total_endpoints": 0,
    "total_features": 0
  },
  "screens": [
    {
      "screen_id": "",
      "route": "",
      "file": "",
      "name": "",
      "group": "",
      "purpose": "",
      "features": [
        {
          "id": "",
          "name": "",
          "description": "",
          "type": "data_display|user_action|navigation|real_time|computation",
          "api_dependencies": [],
          "store_dependencies": [],
          "components": []
        }
      ]
    }
  ],
  "api_contracts": [
    {
      "endpoint_id": "",
      "method": "",
      "path": "",
      "description": "",
      "params": {},
      "response_shape": "",
      "consumers": [],
      "features_enabled": [],
      "category": ""
    }
  ],
  "cross_reference": {
    "screen_to_api": {},
    "api_to_screen": {}
  }
}
```

---

## Quality Check

- [ ] `features.md` generated and saved to project root
- [ ] `features.json` generated and saved to project root
- [ ] Scan scope respected (only INCLUDE files scanned, EXCLUDE files ignored)
- [ ] Every screen in `app/` (except `_layout.tsx`, `+not-found.tsx`) cataloged
- [ ] Every API endpoint identified (OpenAPI + grep)
- [ ] Features have unique IDs (`screen_id_feature_name` pattern)
- [ ] API dependencies bidirectionally mapped (screen→API and API→screen consistent)
- [ ] No orphan screens (zero features) and no orphan endpoints (zero consumers)
- [ ] Feature types consistently classified
