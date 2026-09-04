# Phase 3: Extract by API Contracts (LLM-Assisted)

For each API endpoint, map its capabilities and consumers. Uses api_inventory from Phase 1 and screen features from Phase 2 as input.

---

## Process

```
For each endpoint in api_inventory:
  1. Read OpenAPI spec entry (if available)
  2. Grep for endpoint usage across INCLUDED .tsx/.ts files only
  3. Optionally read api_*_response.json for response shape context
  4. Extract:
     - Request params and body shape
     - Response shape (from spec or sample responses)
     - Business logic / what capability it provides
     - Which screens consume it (from Phase 2 cross-reference)
     - Which features depend on it
  5. Cross-reference with Phase 2 screen features
```

---

## API Feature Schema

```json
{
  "endpoint_id": "get_items",
  "method": "GET",
  "path": "/api/items",
  "description": "Real-time item listing with recommendations",
  "params": { "category": "string (comma-separated category codes)" },
  "response_shape": "Item[] with score, rating, provider",
  "consumers": ["dashboard", "portal", "search_tool"],
  "features_enabled": ["dashboard_item_list", "portal_analysis"],
  "category": "core_data"
}
```

---

## API Categories

Group endpoints by business domain:

| Category | Covers |
|----------|--------|
| `core_data` | Primary entities, listings, details |
| `analytics` | Computed metrics, trends, comparisons |
| `ai_analysis` | AI recommendations, chat, insights |
| `user_data` | Portfolio, history, settings, auth |
| `reference` | Categories, providers, status |
| `social` | Leaderboard, sharing, community |
| `subscription` | Tiers, purchases, entitlements |

Adapt categories to the specific app — these are starting examples for a data-driven mobile app.

---

## Quality Check

- [ ] Every endpoint in api_inventory has been mapped
- [ ] No orphan endpoints (endpoints consumed by zero screens)
- [ ] Consumers list bidirectionally consistent with Phase 2 (screen→API, API→screen)
- [ ] Response shape documented for every endpoint (from spec or grep)
- [ ] Endpoints grouped into business domain categories
