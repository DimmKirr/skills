---
name: drawio-diagram
description: Use when working with .drawio diagrams — creating new architecture diagrams from scratch, cleaning up layout, analyzing positioning, fixing alignment or spacing issues, editing connectors, checking border overlaps, or any task involving mxGraphModel XML
---

# Draw.io Diagram Skill

Work with .drawio architecture diagrams — create, clean up, analyze, and fix.

## Input

The user provides a path to a `.drawio` file (or it can be inferred from the current project context).

## Style Reference

Read [references/style-guide.md](references/style-guide.md) for shape conventions, color scheme, arrow semantics, and label formatting. Load it when creating diagrams, checking visual consistency, or adding new elements.

## Examples (for creating from scratch)

When creating a new diagram, read the appropriate example and reuse its exact style strings:

- **Generic architecture**: [references/examples/example-generic.drawio](references/examples/example-generic.drawio) — all common shapes (rounded rect, cylinder, hexagon, parallelogram, cloud, swimlane, queue), color roles, and arrow styles (solid, dashed, dotted)
- **AWS architecture**: [references/examples/example-aws.drawio](references/examples/example-aws.drawio) — `mxfile` wrapper, `mxgraph.aws4` icon shapes (ECS, Fargate, Lambda, Aurora, OpenSearch, S3, Secrets Manager, Bedrock, ECR) using both `resourceIcon` and `productIcon` patterns, containment hierarchy (AWS Cloud → VPC → AZ → Public/Private Subnet), NAT Gateway, external actors (Users, Internet cloud), 3 arrow types (solid network, dashed internal, `dashPattern=8 8` service integration with service-colored strokes), and legend box

Copy style strings character-for-character from examples — the `mxgraph.aws4` styles are complex and must be exact.

**AWS icon lookup**: Grep [references/aws4-shapes.txt](references/aws4-shapes.txt) to find the exact shape name for any AWS service (1032 shapes, Jan 2026). Convert spaces to underscores for `resIcon`/`prIcon` values. See [references/aws4-icons.md](references/aws4-icons.md) for category colors and group container shapes.

## Approach

**Work directly with the XML** — do NOT attempt Playwright/browser export. The drawio XML is a structured mxGraphModel that can be fully understood, analyzed, and edited as XML. Parse it, compute positions mathematically, identify violations, and write corrected XML.

**Analysis-first workflow**: Complete Phase 1 (position computation) and identify ALL violations across Phases 2-4 BEFORE making any changes. This prevents cascading surprises (e.g., nudging a node for label clearance on one edge may shrink the gap on an adjacent labeled edge).

**Applying changes**: When fewer than 5 edits are needed, use the Edit tool. When 5+ edits are needed (common for a full cleanup pass), use the Write tool to output the entire corrected file in one shot — this avoids uniqueness conflicts with repeated patterns like `x="15"`.

**Cascade principle**: After any node position change, immediately re-check: (1) all edges to/from the moved node for label clearance and gap violations, (2) container padding if inside a group, (3) proportional spacing with siblings. Moving a node to fix one issue can create violations elsewhere — compute the full cascade chain before applying.

## Triage

Before diving into the workflow, assess the diagram and clarify scope with the user if needed.

**Ask the user when:**
- The diagram has **3+ distinct arrow styles** — ask: "This diagram uses semantic arrow styles (solid=sync, dashed=async, dotted=scheduled, thick-red=critical path). Should I preserve these conventions, or normalize to a simpler scheme?"
- The diagram has **no legend** but uses 4+ shape/color types — ask: "This diagram uses N distinct visual styles but has no legend. Should I add one?"
- The task is ambiguous between **cleanup vs. creation** — ask: "Should I clean up the existing layout, or restructure/rebuild the diagram?"
- The diagram uses **`page=0`** (infinite canvas) — note this in analysis; spacing rules still apply but there are no page bounds to check against.

**Do NOT ask when:**
- The user gave a specific task ("fix alignment", "add a legend", "clean up connectors")
- The diagram is simple (<15 nodes) with a single arrow style
- You're running the full cleanup workflow (just execute it)

**Creation triage** (when building a diagram from scratch):

1. **Diagram type** — ask which focus:
   - Architecture overview (services, databases, integrations, data flow)
   - Network topology (VPCs, subnets, security groups, NACLs, routing tables)
   - Deployment / infrastructure (containers, Fargate, ALBs, auto-scaling groups)
   - Data flow / ETL pipeline (S3, Kinesis, Lambda, Glue, Redshift)
   - Security (IAM, WAF, KMS, encryption, GuardDuty)
   - CI/CD pipeline (build → test → deploy stages)
   - Process / sequence flow (step-by-step workflow, state machines, decisions)

2. **External actors** — what connects from outside? (users, Internet, third-party APIs, other AWS accounts, on-premises)

3. **Backing services** — any databases, caches, storage, queues, or AI/ML services?

4. **Connection patterns** — main data flows? (request path, async events, scheduled jobs, replication)

**Mermaid fast-path assessment** — after gathering the above, assess whether native XML or Mermaid-then-convert is better. Tell the user your recommendation and why:

| Signal | Recommendation |
|--------|---------------|
| Simple flowchart, sequence, or state diagram with <15 nodes | **Mermaid** — faster, auto-layout handles it well |
| Org chart or tree hierarchy | **Mermaid** — `graph TD` or CSV import handles this naturally |
| Needs AWS/cloud icons, custom shapes, or `mxgraph.*` stencils | **XML** — Mermaid has no icon library support |
| Needs precise positioning (subnet containment, AZ grouping) | **XML** — Mermaid auto-layout can't do nested containers |
| Needs specific colors, line styles, or legend | **XML** — Mermaid styling is limited |
| >20 nodes with complex cross-connections | **XML** — Mermaid auto-layout gets messy at scale |
| Mixed: simple flow + a few custom shapes | **XML** — partial Mermaid doesn't save effort |

Example recommendation: "This is a 3-AZ AWS architecture with subnets, Fargate, and ALB — I'd recommend native XML because we need AWS icon shapes and nested containment groups. Mermaid can't do that."

Example recommendation: "This is a straightforward CI/CD pipeline with 6 sequential stages — Mermaid would be faster here and auto-layout will handle it cleanly. Want me to use Mermaid?"

**When using Mermaid**: Write a `.mmd` file with the Mermaid source code. Tell the user to import it into draw.io via **Extras > Edit Diagram**, paste the Mermaid code, and click OK — draw.io converts it to native shapes. After import, the diagram becomes editable draw.io XML (the original Mermaid source is not preserved). Note: there is no reliable way to embed Mermaid in a `.drawio` XML file that auto-renders on open.

## Phase 1: Parse & Compute

### 1. Read and Parse the XML

Read the `.drawio` file. Identify:
- **File wrapper**: The file may be bare `<mxGraphModel>` or wrapped in `<mxfile><diagram>...<mxGraphModel>`. The `<mxfile>` wrapper is standard for draw.io desktop (includes `host`, `agent`, `version` metadata) and is required for multi-diagram files. When creating files, use the `<mxfile>` wrapper for compatibility. When editing, preserve whichever wrapper the file already uses.
- `page` attribute from `<mxGraphModel>`: `page=1` (fixed page, check bounds) vs `page=0` (infinite canvas, skip page bounds)
- `pageWidth` / `pageHeight` from `<mxGraphModel>`: choose based on diagram complexity. Common sizes: 1169x827 (A4 landscape, simple), 1400x1000 (medium), 1600x1200 (complex with detail panels). When creating, pick the smallest size that fits with comfortable margins.
- `gridSize` from the `<mxGraphModel>` attributes (typically 10)
- All vertex cells (`vertex="1"`) — extract id, value (label), parent, style, and geometry (x, y, width, height)
- All edge cells (`edge="1"`) — extract id, value (label), parent, source, target, style, and any waypoints (`<mxPoint>` inside `<Array as="points">`)
- **Edge label child cells**: draw.io's interactive editor creates labels as separate `edgeLabel` cells with `connectable="0"` and `parent` set to the edge ID, rather than setting `value` on the edge itself. Detect both patterns. See Label Formatting in style-guide.md for the full XML structure.
- Parent hierarchy: cells with `parent="1"` are top-level; cells whose parent is another vertex are children of that container/group
- **Visual-only groups** (`container=0`): Some group cells use `container=0;connectable=0` — these are visual boundary boxes only. Their "children" are NOT parented to the group in XML (they use `parent="1"`). These groups affect visual appearance but NOT the coordinate system. During position computation, do NOT recurse into `container=0` groups for child offsets — treat their enclosed nodes as top-level.

### 2. Compute Absolute Positions

Build an absolute position table for every node. Children of groups/containers have positions **relative to the parent**, so add the parent's absolute position:

```
absolute_x = parent_abs_x + child_relative_x
absolute_y = parent_abs_y + child_relative_y
center_x   = absolute_x + width / 2
center_y   = absolute_y + height / 2
```

For nested groups, recurse up the parent chain. Top-level nodes (parent="1") use their geometry directly.

**Output the positions as a table** grouped by parent, showing: ID, Label, Absolute (x,y), Size (w*h), Center (cx,cy), Shape type. This table is the foundation for all subsequent analysis.

**Also compute edge endpoints**: For each edge, determine the absolute positions of source and target, then compute `dx = |target_center_x - source_center_x|` and `dy = |target_center_y - source_center_y|`.

---

## Phase 2: Spacing & Layout

All node position changes happen in this phase. Finalize every node's position before moving to Phase 3 (connectors).

### 3. Node Alignment

For every edge with `edgeStyle=orthogonalEdgeStyle`, use the dx/dy from Step 2.

**Categorize:**
- **Fixable**: dx < 30 OR dy < 30 (nudge the smaller offset to zero)
- **Structural**: both dx > 30 AND dy > 30 (L-shape is unavoidable)

**Fix by nudging nodes** so connected nodes share the same center X or center Y.

**Height mismatch rule**: Nodes of different heights (e.g., datastore h=60 vs rounded rect h=40) have different center offsets even when on the "same row." Fix by adjusting Y positions so `y + h/2` matches. Example: a datastore at y=470 h=60 has center_y=500; a rounded rect sharing the row needs y=480 h=40 to also get center_y=500.

**Fan-in alignment priority**: When multiple sources feed into one target from the same side (e.g., Source 1/2/3 -> Integration), prioritize aligning the **middle/central** source for a perfectly straight connector. The outer sources will naturally L-bend and that's acceptable. After aligning the middle source, equalize spacing between all sources for visual balance.

**Same-role stacking rule**: Connected elements of the same fill color arranged primarily vertically (dy > dx) should share `center_x`. Same-color elements arranged horizontally (dx > dy) should share `center_y`. This check applies **even when the offset exceeds 30px** — the "structural" classification does not exempt same-role pairs from alignment.

**Alignment constraint-chain tracing**: When alignment is blocked by an adjacent gap constraint, do NOT accept the blocker at face value. Trace the constraint chain: is the blocking node itself free to move? Apply the same degrees-of-freedom principle from Step 4c — an alignment offset is truly structural ONLY when the entire constraint chain is pinned. Example: Node A center_x=1010, Node B center_x=1050 (pinned by Node C gap). But Node C has no constraint anchoring its x-position — moving Node C left 40px frees Node B to align with Node A, eliminating a 2-bend Z-bend entirely.

### 4. Gap Sizing

Every gap between connected nodes has one correct size: the **minimum viable gap**. Compute it per edge, then enforce it.

#### 4a. Compute the target gap per edge

For unlabeled edges:
```
target_gap = 4 grid squares (40px)
```

For labeled edges (edges with a non-empty `value` attribute), estimate label clearance:
```
label_width = max_line_chars * 6px    # at fontSize=10, conservative
target_gap  = max(40px, label_width + 2 * gridSize)
```

For multi-line labels (`&#xa;` delimiter), use the widest line.

**Label positioning rule**: Labels must always be centered on the middle of the connector line (default mxGraph positioning). Never use `<mxPoint as="offset"/>` to shift labels.

**Relevant segment for L-bend labels**: The label sits at the path midpoint — identify which segment contains the midpoint and use that segment's length. If the midpoint falls on a long vertical segment, the label renders horizontally — focus on ensuring it doesn't overlap nearby nodes.

**Conservative estimate tolerance**: Since 6px/char is conservative (actual ~5.5px), a gap 2-4px short of the target is acceptable. Only nudge when the shortfall exceeds 4px.

#### 4b. Measure actual gaps

**Connected-node gaps** (edge-by-edge): For every edge, compute the gap vector:
```
gap_x = target_x - (source_x + source_w)    # horizontal clearance
gap_y = target_y - (source_y + source_h)     # vertical clearance
```

Use the **relevant axis** for the connector direction:
- Horizontal connector (same center_y): check `gap_x`
- Vertical connector (same center_x): check `gap_y`
- L-bend: check both axes independently

**Row/column gaps** (neighbor-by-neighbor): Within each group/container, identify logical **rows** (nodes sharing similar center_y, +/-20px tolerance) and **columns** (similar center_x). Measure gaps between adjacent rows/columns:
```
row_gap = next_row_min_y - current_row_max_bottom
col_gap = next_col_min_x - current_col_max_right
```

This catches excessive gaps between tiers that may not have direct connectors.

#### 4c. Fix violations

Flag any gap where `actual_gap != target_gap` (too small OR too large).

**Too small**: Nudge the target node away. Cascade all downstream nodes by the same amount.

**Too large — categorize:**
- **Fixable**: No structural constraint prevents closing the gap. Move the further node/row closer.
- **Structural**: The gap exists because of an external constraint (fan-in alignment, label clearance on another edge, column alignment).

**Challenge every structural classification** (degrees of freedom analysis — applies to BOTH gap sizing AND alignment):

A gap or alignment offset classified as "structural" means one side is pinned — it does NOT mean the gap/offset is irreducible. Check if the OTHER side is free to move closer:

1. **Identify the pinned side and the free side.** A node/row is "pinned" if moving it would violate an alignment constraint. A node/row is "free" if no constraint anchors it.

2. **Check free-side mobility:**
   - **Connections**: Do all edges go toward (or past) the pinned side? If yes, moving closer is strictly better.
   - **Siblings**: If part of a row, all siblings must move together without new violations.
   - **Container bounds**: If inside a group, the container can shrink from the vacated side.
   - **Path clearance**: No other nodes occupy the target space.

3. **Calculate**: `move_distance = current_gap - target_gap`, round to grid.

4. **Cascade**: Update waypoints, shrink containers, re-check all connected edges.

**Key principle**: A gap or alignment offset is truly irreducible ONLY when BOTH sides are pinned. When an alignment blocker is itself a movable node, trace the full constraint chain before accepting "structural."

**Document** any remaining structural gaps with gap vector, constraint, and minimum required gap.

### 5. Proportional Spacing

Identify groups of same-class elements (same fill/stroke color AND shape type, same parent container AND role, or same pipeline level). Within each group, all gaps between consecutive elements must be equal.

**Audit:**
1. Vertical stacks: measure `top_of_next - bottom_of_current` per consecutive pair
2. Horizontal sequences: measure `left_of_next - right_of_current` per consecutive pair
3. Grids within detail panels: check both row gaps AND column gaps independently

**Height-compensated alignment**: When a row contains elements of different heights, check that center_y values match. The taller element's y is adjusted so centers align: `y = row_center_y - h/2`. This is intentional — do NOT "fix" the y-offset.

**Fix** by picking the most common gap value (or the largest if they vary) and normalizing. Respect alignment constraints — the middle source stays aligned with its target (fan-in rule from Step 3).

**Group centering rule**: After equalizing gaps, verify the group is centered on its connection target. E.g., a vertical group's collective center_y should match the target node's center_y.

### 6. Container Padding

Check that all child elements inside groups/containers have at least **2 grid squares (20px)** of padding from the container border on all four sides.

```
left_pad   = child_x                          >= 20
top_pad    = child_y                          >= 20
right_pad  = container_width - (child_x + w)  >= 20
bottom_pad = container_height - (child_y + h) >= 20
```

**Swimlane startSize note**: Swimlanes have a header bar of `startSize` pixels (typically 25). Children are positioned relative to the full container including the header. A child at y=40 in a swimlane with startSize=25 has 15px of visual padding below the header — but the rule checks `child_y >= 20` without subtracting startSize, so y=40 passes.

**Fix by expanding the container outward**, not by squishing children inward:
1. Calculate the maximum violation on each side
2. Shift the container origin by that amount
3. Increase container dimensions to compensate
4. Add the offset to ALL children's relative coordinates

This preserves all absolute positions — edges with `parent="1"` use absolute coordinates, so no waypoint changes are needed.

**Also update alternateBounds**: If the container has an `<mxRectangle as="alternateBounds">`, update its x/y to match.

**Note:** When a child geometry omits `x` or `y` attributes, mxGraph defaults them to 0. These elements are flush with the container border and need the padding fix.

---

## Phase 3: Connectors

All edge routing changes happen in this phase, after node positions are finalized in Phase 2.

**Edge hygiene (pre-check)**: Before analyzing routing, clean up edge artifacts:
- Connected edges (with `source`/`target` attributes) must NOT retain stale `<mxPoint as="sourcePoint"/>` or `<mxPoint as="targetPoint"/>` elements — remove them
- Remove redundant zero-value style attributes: `exitDx=0;exitDy=0;entryDx=0;entryDy=0` (these are defaults)
- After converting a floating edge to connected, recompute waypoints from current node positions — old waypoints reference stale coordinates and may route to wrong locations

### 7. Side-Center Exits & Entries

Edges must exit and enter from the **center of a side** — never from corners. Corner exits like `exitX=1;exitY=1` create visually awkward diagonal-looking departures.

Valid exit/entry points (side centers only):
- Top center: `exitX=0.5;exitY=0`
- Right center: `exitX=1;exitY=0.5`
- Bottom center: `exitX=0.5;exitY=1`
- Left center: `exitX=0;exitY=0.5`

Choose the side that faces most directly toward the target.

**Fine-tuned values**: Entry/exit values are continuous 0.0–1.0, not limited to the standard 0/0.25/0.5/0.75/1 set. Use fine-tuned values like `entryX=0.05` or `exitY=0.3` when routing demands it (e.g., avoiding overlaps on a specific side, connecting to a precise position on a wide node). Prefer standard values when they work; use fine-tuned values only when standard values cause routing problems.

**Exceptions allowing non-center entry/exit:**
- **Color separation (Step 10)**: Two edges of different colors entering the same side — offset to `entryY=0.75` or `entryY=0.25`
- **Fan-in separation**: 3+ edges entering the same side of a wide node — distribute entry points (e.g., `entryY=0.25`, `entryY=0.5`, `entryY=0.75`) to avoid stacking
- **Semantic clarity**: When a node has distinct input zones (e.g., a wide API box receiving data from left and clients from right), offset entry hints improve readability

### 8. Minimize Bends

For each edge, calculate the theoretical minimum number of bends:
- **0 bends**: Source and target share an axis (same center_x or center_y) — straight line
- **1 bend**: A clear L-path exists with no obstacles
- **2+ bends**: Only when obstacles block all simpler routes

**Verification procedure:**
1. Compute all possible 0-bend paths (straight line from each side center pair that shares an axis)
2. Check if the line segment passes through any non-source/non-target node bounding box
3. If blocked, compute all 1-bend L-paths (exit side * enter side combinations forming an L)
4. Check if either segment passes through a node
5. If all 1-bend paths blocked, find the 2-bend route through the widest gap

Remove explicit waypoints that exceed the minimum bend count. When the auto-router can produce the optimal path with just exit/entry hints, **remove all waypoints entirely**.

**Waypoint micro-bend check**: Verify the first waypoint aligns with the exit point and the last aligns with the entry point. A waypoint at (420, 660) when the exit y is 670 creates a needless 10px jog. Fix by aligning.

### 9. Fix Edge Crossings & Border Overlaps

Trace each edge's orthogonal path. Check two things:

**A. Node crossings**: Does any segment pass through a non-source/non-target node's bounding box?

**B. Border overlaps**: Does any segment run along (overlap or near-overlap) a container/group border? Compute the distance from each edge segment to every container border segment on the same axis:
- Horizontal edge segment at y=Y vs horizontal border at y=B: `|Y - B|`
- Vertical edge segment at x=X vs vertical border at x=B: `|X - B|`

Flag when distance < 10px AND the segments overlap in the perpendicular axis range. An edge running on top of or within a few pixels of a dashed group border or swimlane border is visually confusing.

**Common case — fan-in L-bends at group boundaries**: When external nodes (e.g., sources) connect to a node just inside a container, the auto-router's L-bend turn point lands exactly on the container border. Fix by adding explicit waypoints that place the vertical segment 10px outside the border. Example: sources at x=40-140 connecting to a node at x=180 inside a group with left border at x=160 — add waypoints at x=150 to force the turn 10px outside.

**Common case — external actors to internal nodes**: When nodes outside a major container (e.g., Internet cloud at x=20-140) connect to nodes inside (e.g., IGW at x=260, Route53 at x=260), the auto-router's L-bend vertical segment lands exactly on the container's left border. Fix by adding explicit waypoints that stagger the vertical segments **outside** the container border with 10px separation between parallel edges. Example: Internet→IGW (blue, thick) routes at x=180, Internet→Route53 (purple, thin) routes at x=170 — both clear the AWS Cloud border at x=200 with 20-30px margin, and the 10px gap between x=170 and x=180 keeps the two edges visually distinct. Similarly, Vercel→ALB routes at x=190 to avoid crossing through the Internet cloud node.

**Fix by rerouting** — add or adjust waypoints to maintain >= 10px clearance from all container/group borders:
- Route through gaps between adjacent nodes (>= 20px clearance)
- Prefer natural gaps over long detours
- Use `exitX`/`exitY` style attributes to force the exit side

**Waypoint coordinate system**: Waypoints use the coordinate system of the edge's `parent`. If `parent="1"`, absolute page coordinates. If `parent="some-group"`, relative to that group's origin. Always check the edge's parent.

**Waypoint format:**
```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="435" y="400" />
  </Array>
</mxGeometry>
```

### 10. Shared Exit Points & Color Overlaps

**Shared exits**: When multiple edges exit from the same side of a node, the auto-router stacks them at the same point.

**Fix with hints** to separate exit points:
- The straight-line edge keeps the default exit
- The angled edge gets an explicit exit from a different side

**Acceptable overlap**: When two edges immediately diverge, the auto-router's jettySize separates them enough. Only fix when paths stack for > ~20px.

**Parallel edge stacking**: When multiple edges from different source nodes run to the same region (e.g., flux→opensearch and indexer→opensearch), their horizontal waypoint segments often stack within 5px of each other. This creates a visual band of overlapping lines. Fix by spreading waypoint Y-coordinates at least 15-20px apart. Example: three edges at y=608, y=613, y=630 should be spread to y=598, y=620, y=645. Similarly, horizontal RDS-bound edges in a gap zone (e.g., y=835-855) should be spread across the full available gap (e.g., y=820, y=840, y=860, y=875).

**Different-color overlaps**: Catalog edges by `strokeColor`. When two edges of different colors share a path segment (not just crossing at a point):
- Keep the primary edge at the default entry point
- Offset the secondary edge's entry using `entryY=0.75` or `entryY=0.25`
- Adjust the nearest waypoint to match
- This creates ~10px visual separation

**See Step 7 for the full list of exceptions to the side-center rule.**

### 11. Explicit Exit/Entry Hints

For every edge with waypoints or a non-straight path, add explicit `exitX`/`exitY` and `entryX`/`entryY` style attributes. This prevents the auto-router from choosing a suboptimal side on re-open.

**When hints are NOT needed**: 0-bend straight paths on the main axis — the auto-router handles these correctly.

**When hints ARE needed:**
- Any structural L-bend (both dx > 30 and dy > 30)
- Any edge with explicit waypoints
- Any edge routing around obstacles

---

## Phase 4: Visual Polish

### 12. Symmetry and Balance

Review the position table for overall visual balance:

**Pipeline spacing consistency**: Measure gaps between consecutive pipeline nodes. Normalize to consistent spacing. Labeled connectors constrain minimum gaps, so spacing won't always be perfectly uniform.

**Column alignment**: Vertically stacked elements should be center-aligned. Check that `center_x` matches. Fix width inconsistencies — elements of the same type should have similar widths.

**Container centering**: Sources or other elements feeding into a swimlane should be vertically centered on it.

**Weight distribution**: Detail panels and auxiliary elements shouldn't cluster on one side.

**Element width consistency**: Rounded rectangles of the same role: 80-100px. Datastores: 70-80px. When two same-role elements are connected by a direct edge and arranged vertically, width mismatch directly causes center_x misalignment. Prioritize matching widths for connected same-role pairs — a 20px width difference creates a 10px center offset that forces a Z-bend.

### 13. AWS Icon Labeling

AWS resource icons (`shape=mxgraph.aws4.resourceIcon`) should be labeled with the **resource/instance name**, not the service name. The icon shape already communicates the service type — adding "S3" or "Lambda" as the label is redundant.

**Idiomatic pattern**: `ever-cars-experimental` (resource name) instead of `S3 / ever-cars-experimental` (service name + resource name).

**When no resource name exists** (e.g., a single CloudWatch or ACM instance), the service name is acceptable as the label since it serves as the identifier.

**Label style**: Plain text at `fontSize=9`, no bold. The icon is the visual anchor; bold on the label competes with it. Use `<font style="font-size: 9px;">resource-name</font>` for consistency.

**ECS service labels**: For Fargate task icons, use just the service name (e.g., `flux`, `indexer`, `chat-api`) — no CPU/MEM/port details. Those belong in documentation, not the architecture overview.

### 14. Arrow Color Deconfliction

Edge `strokeColor` values must NOT match any block/container `strokeColor` in the diagram. When an arrow color matches a container border color, the arrow visually merges with the border, creating confusion.

**Audit procedure**: Catalog all vertex `strokeColor` values (block borders) and all edge `strokeColor` values. Flag any matches. Replace conflicting edge colors with a darker/lighter variant of the same hue that maintains semantic meaning.

**Example replacements** (from AWS architecture diagrams):
| Edge semantic | Conflicting color (= block border) | Replacement |
|---|---|---|
| DNS/routing | `#8C4FFF` (= VPC border) | `#5A189A` (deep purple) |
| Data store | `#C925D1` (= RDS icon fill) | `#9B2335` (dark rose) |
| Service integration | `#d6b656` (= external block border) | `#B8860B` (dark goldenrod) |
| Lambda/compute | `#ED7100` (= ECS cluster border) | `#CC5500` (burnt orange) |
| Internal/helper | `#666666` (= Internet cloud border) | `#404040` (charcoal) |
| VPC peering | `#6c8ebf` (= VPC box border) | `#2E5984` (dark steel blue) |

When changing edge colors, also update the legend entries and any inline font color in edge labels.

### 15. Layout Optimization Principles

When cleaning up or creating architecture diagrams, apply these principles to minimize line crossings and bends:

**3-tier architecture layout**: Most infrastructure diagrams follow a 3-tier pattern. Arrange tiers as strict horizontal bands:

| Tier | Y band | Contains | Arrow direction |
|---|---|---|---|
| **Ingress** (top) | y=100-400 | Route53, CloudFront, ALBs, IGW | Arrows enter from top/left |
| **Compute** (middle) | y=400-800 | ECS/EKS services, Lambda, containers | Arrows exit to right/bottom |
| **Messaging** (optional) | y=600-800 | SQS, SNS, Kafka, RabbitMQ, EventBridge | Between compute and data |
| **Data** (bottom) | y=800-1100 | RDS, ElastiCache, OpenSearch, S3 | Arrows enter from top |

Traffic flows top-to-bottom. All nodes in a tier share the same Y. External actors (Users, Internet, Vercel) sit outside the tiers on the left. External integrations sit outside on the right.

For complex systems with 5+ tiers, expand to: **Ingress → Compute → Messaging → Data → External integrations** (left-to-right for the last tier, or as a separate column on the right side of the diagram).

**Reading direction**: The diagram reads left-to-right, top-to-bottom — like text. This means:
- Arrows entering a box should land on the **LEFT side** or **TOP side**
- Arrows leaving a box should exit from the **RIGHT side** or **BOTTOM side**
- Horizontal segments should go left-to-right when possible (right-to-left is a violation unless structurally unavoidable)
- When a connection must go right-to-left (e.g., chatapi → rds-evercars), route it via a vertical drop then leftward horizontal at the data tier — not a long horizontal segment through the compute tier

**Adjacency minimizes bends**: Position each node near its primary connection partner. If Lambda is called only by flux, place Lambda adjacent to flux — not in a distant stack. A straight horizontal line is always better than a 3-bend detour.

**Single service row when possible**: Prefer placing all compute services on one horizontal row rather than splitting into multiple rows. Multiple rows create crossing opportunities when edges from an upstream node (ALB) must reach services in different rows.

**Fan-out nodes above their targets**: When one node (ALB) connects to many targets (services), center it above the targets and use vertical drop-down connections. This avoids horizontal edges crossing over sibling nodes. Each fan-out edge should enter its target from TOP.

**Unified data tier**: Place ALL persistent stores (RDS, caches, search) on the same horizontal band below the services. Don't scatter data stores to the right — that creates long horizontal runs and parallel edge stacking.

**Container sizing matches content**: Resize AWS Cloud, VPC, subnet containers to tightly wrap their content (20px padding). Oversized containers waste space and make edge routes longer.

**Isolated specialty nodes**: Nodes with few connections (e.g., a workflow engine like Cadence) can sit on their own row below the main service row, reducing congestion in the primary row.

**Use proper XML grouping**: When a set of nodes belongs together (e.g., External Integrations), use a `group` container so children use relative coordinates. The group moves as a unit and the XML is cleaner. Do NOT use flat `parent="1"` with absolute coordinates for logically grouped items.

**Visual hierarchy via stroke weight**: Use `strokeWidth=2` for important container borders (ECS cluster, security groups) to distinguish them from edge lines at `strokeWidth=1`.

**Minimum gap between boxes**: Every pair of adjacent nodes must have at least **2 box-sizes** of clear space (100px for standard 50px icons). This includes both horizontal and vertical gaps. Tight spacing makes labels overlap and edges impossible to route cleanly.

**L-bend minimum knee length**: Every bend in an orthogonal connector must have at least **1 grid square** (10px) of straight segment at the knee. A bend with 0px or 2px of straight segment before the next turn looks like a glitch, not intentional routing.

### 16. Legend & Annotations

**Legend**: Diagrams with 4+ distinct shape/color combinations should have a legend box. Place it in a corner (typically top-left) using a dashed container with light gray fill. Include one example of each shape+color combination with label, and one example of each arrow style with label (Synchronous, Asynchronous, Scheduled, Critical Path, etc.).

**Text annotations**: Use free-standing `text` cells (no edge connections) for:
- Timing/latency info near critical path edges (e.g., "Poll every 5s", "Push 5s")
- Protocol/channel details near connection points (e.g., "AMQP", "WebSocket /v1/game_connect/{id}")
- Pipeline pattern descriptions near repeated patterns (e.g., "Streamer -> CBuffer -> Harvester")
- Architecture boundary labels on container groups (e.g., "AWS ECS Fargate (Terraform-managed)")

**Critical path callout**: For systems with latency-sensitive flows, add a prominent annotation box (colored border, light fill) tracing the end-to-end path with timing at each hop. Place it below or beside the main diagram area.

**Detail panel pattern**: For complex nodes that need expanded internals, use a **summary node** in the main flow (compact rounded rect) linked to a **detail panel** elsewhere on the canvas (typically below the main flow). The detail panel is a swimlane container with neutral styling (`fillColor=#f5f5f5;strokeColor=#666666`) containing the expanded sub-components. Use `fontSize=8` for detail panel children to visually distinguish them from the main flow. The summary node and detail panel share a label (e.g., "Integration" in both places).

**Repeating row pattern**: When a detail panel contains N instances of the same pipeline (e.g., Client -> Raw Store -> Normalize), arrange them in uniform rows with:
- Consistent horizontal spacing between pipeline stages within each row
- Consistent vertical spacing (row gap) between rows
- Matching styles across all instances (same width, height, fill, stroke)
- Row gaps of 20-30px between consecutive pipeline rows

**Detection during cleanup**: Check for orphan text cells that no longer align with their referenced components after node repositioning. When moving nodes, also reposition nearby text annotations to maintain visual association.

---

## Phase 5: Verify

Load [references/verification.md](references/verification.md) for the full verification checklist (spacing, connectors, visual) and the complete rules list. The verification step includes mandatory PNG export + LLM visual review — do NOT skip it.
