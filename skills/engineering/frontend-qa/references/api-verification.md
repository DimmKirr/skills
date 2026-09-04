# API Verification Reference

## Schema Freshness

### How to Check if `openapi.json` is Stale

1. **Compare field names** — fetch a live endpoint, list top-level keys, compare to schema:

```bash
# Live response keys
curl -s "$API_BASE/api/v1/<resource>?<params>" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[0] | keys'

# Schema fields for the same response type
grep -A5 '"ResourceResponse"' openapi.json
```

2. **Check git blame on `openapi.json`** — if it's older than recent API deploys, it's likely stale:

```bash
git log --oneline openapi.json | head -5
```

3. **Re-download the schema** — the API typically serves its own spec:

```bash
curl -s "$API_BASE/openapi.json" -o openapi.json
# or
curl -s "$API_BASE/api/openapi.json" -o openapi.json
```

4. **Regenerate TypeScript types** after updating schema:

```bash
npx openapi-typescript openapi.json -o src/api/schema.ts
```

### Common Field Rename Patterns

These renames cause silent `undefined` bugs — watch for them after any API update:

| Pattern | Example | Impact |
|---------|---------|--------|
| Shortened name | `item.time` → `item.start_time` | Components destructure wrong key |
| Semantic rename | `amount` → `total` | Multiple components + stores affected |
| Nested key change | `stats.confidence` → `stats.probability` | Display components show `undefined` |
| Removed field | `stats.estimate` → _(removed)_ | Components crash or show NaN |
| Scale change | Percentage `85` → ratio `0.85` | Display shows wrong values, not `undefined` |

**Scale factor changes** are especially dangerous — no crash, no `undefined`, just wrong numbers. If a field changes from percentage to ratio, multiply by 100 for display.

---

## Direct API Testing

### First rule: hurl files trump ad-hoc curl

If `apps/core/integration/**/*.hurl` exists, those files are the canonical contract for every endpoint. Run them directly, or copy field names from their `[Asserts]` blocks before writing curl.

```bash
# 1. Run the matching hurl file (preferred):
hurl --test --variables-file apps/core/integration/vars.dev \
     --variables-file /tmp/cached_jwt \
     apps/core/integration/<area>/<endpoint>.hurl

# 2. If you must write curl, find the contract first:
find apps/core/integration -name "*.hurl" | xargs grep -l "<endpoint-path>"
grep "jsonpath" apps/core/integration/<area>/<file>.hurl
# Use those field names verbatim in jq. Never guess from the URL path.
```

If no hurl file exists for an endpoint, read the route handler's `response_model` class in the backend source. Still don't guess.

**Why this matters:** A URL path like `/resources/{id}/items` might return `{resource_id, entries: [...]}` — NOT `{items: [...]}`. Probing with guessed keys returns null and leads to false root-cause analysis. Always read the contract first.

### Auth Flow (JWT-based)

If the project uses JWT auth with a cached-token pattern:

```bash
export API_BASE="<your-api-base-url>"

# Mint + cache the JWT (reuse for ~50 min):
hurl --variables-file apps/core/integration/vars.dev \
     --json apps/core/integration/_auth-once.hurl \
  | jq -r '.entries[-1].captures[] | "\(.name)=\(.value)"' > /tmp/cached_jwt

TOKEN=$(grep -oP 'token=\K.*' /tmp/cached_jwt)
echo "TOKEN=$TOKEN"
```

### Key Endpoint Patterns

```bash
# List resources (with filters)
curl -s "$API_BASE/api/v1/<resource>?<filter>=<value>&date=YYYY-MM-DD" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[0]'

# List by status
curl -s "$API_BASE/api/v1/<resource>?status=active" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[0]'
```

### Category/Filter Differentiation Test

To verify different filter values return different data (backend correctness):

```bash
for category in category_a category_b category_c; do
  echo "=== $category ==="
  curl -s "$API_BASE/api/v1/<resource>?category=$category&date=YYYY-MM-DD" \
    -H "Authorization: Bearer $TOKEN" \
    | jq '[.total, .items[0] | keys[:3]]'
done
```

Expected: different `total` counts, potentially different item shapes.
If all identical → backend bug (file a ticket, do not fix in frontend).

### HURL Test Template

For repeatable API TDD tests, use HURL format:

```hurl
# auth.hurl
POST {{api_base}}/api/v1/auth/token
Content-Type: application/json
{"credentials": "{{credentials}}"}

HTTP 200
[Captures]
token: jsonpath "$.token"

---

# test-endpoint.hurl
GET {{api_base}}/api/v1/<resource>
  ?category=<value>
  &date={{date}}
Authorization: Bearer {{token}}

HTTP 200
[Asserts]
jsonpath "$.items" isCollection
jsonpath "$.items[0].category" == "<value>"
jsonpath "$.items[0].score" greaterThan 0
```

Run with: `hurl --variable credentials=<CREDS> --variable date=YYYY-MM-DD test-endpoint.hurl`
