# Verification Checklist & Rules

## Phase 5: Verify

After writing the corrected XML, re-read it and verify by recomputing positions:

**Spacing & Layout:**
- All connector gaps match their target gap (min viable gap per edge)
- No row/column gaps exceed target without documented structural justification
- All container padding >= 2 grid squares on every side
- Same-class element groups have equal spacing between consecutive members
- Each element group is centered on its connection target
- Stacked elements are center-aligned
- Connected same-role (same fill color) elements share center_x (vertical) or center_y (horizontal)

**Connectors:**
- Main pipeline arrows are straight horizontal (all center_y match)
- Vertical connections are straight vertical (all center_x match)
- No arrows crossing through boxes
- No edge segments running along container/group borders (>= 10px clearance)
- Every connector uses side-center exits/entries (except Step 7 exceptions: color separation, fan-in separation, semantic clarity)
- Every connector achieves minimum possible bend count
- Every labeled connector has >= 1 grid square clearance between label and nodes
- Labels are centered on the line (no offsets)
- No shared exit points causing overlapping arrows
- No different-color connectors sharing the same path segment
- Non-straight connectors have explicit exit/entry hints
- All waypoints align with exit/entry coordinates (no micro-bends)
- Arrow style semantics preserved: if diagram had 3+ distinct edge styles, all styles still match their original convention (see Arrow Semantics)

**Visual:**
- Pipeline spacing is consistent across consecutive nodes
- No new overlaps or visual regressions introduced
- No stale sourcePoint/targetPoint on connected edges
- No redundant zero-value style attributes (exitDx=0, exitDy=0, etc.)
- Shape types match their component role (see Shape Conventions)
- Color fills are consistent within same-role groups (see Color Scheme)
- HTML label format consistent across same-role elements (same `<b>`/`<br>`/`<i>` pattern)
- Legend present if diagram uses 4+ distinct shape/color combinations (see Step 13)
- Text annotations still aligned with their referenced components after repositioning
- No orphan text cells left adrift from moved nodes
- Detail panel repeating rows have uniform spacing and matching styles across instances
- Visual-only groups (`container=0`) not mistakenly treated as containers in position calculations
- Edge labels (both `value` attributes and `edgeLabel` child cells) preserved in their original pattern
- `mxfile` wrapper preserved or added as appropriate for the file format

**Visual verification** (MANDATORY — must be the final step for every diagram change):

All spacing, alignment, style, and layout checks MUST be verified visually via PNG export and LLM review. Mathematical position analysis alone is insufficient — it misses rendering artifacts, label overflow, font sizing issues, and visual weight imbalances that only appear in the rendered output.

1. Export PNG: `drawio --no-sandbox -x -f png --scale 3 -o /tmp/diagram-verify.png input.drawio`
   - `--no-sandbox` required in containers (no SUID sandbox)
   - Do NOT use `--disable-gpu` — it breaks Electron argument parsing
   - `--scale 3` is the sweet spot for LLM vision review (~5000-6000px). Higher scales (4x+) waste tokens — Claude downsamples to ~1568px internally, so anything above 3x gives no extra detail to the model. Lower scales (1x-1.5x) make small text unreadable.
   - **Requires**: a GUI-enabled environment (e.g. a headless container running Xvfb + mesa software rendering)
   - If export fails with "Export failed", reduce scale to 2.5 or check: (1) `/dev/shm` size (`df -h /dev/shm` — needs 1GB), (2) env vars `DISPLAY`, `LIBGL_ALWAYS_SOFTWARE`
   - dbus warnings in stderr are harmless — check for `->` in output to confirm success
2. View the PNG using the `Read` tool (which renders images for LLM vision review). The export is full-page (not cropped) — view it as a person would view the printed/shared diagram
3. **Page-level balance** (assess first, before zooming into details):
   - Is the diagram well-centered on the page? Or crammed into one corner with empty space elsewhere?
   - Is the visual weight distributed evenly? Heavy clusters on one side with sparse areas on another indicate layout imbalance
   - Are margins adequate? Content should not touch or nearly touch page edges
   - Does the page size match the content? A small diagram on a huge page looks lost; a dense diagram on a small page looks cramped
4. **Element-level checks** (after page balance is confirmed):
   - Overlapping labels or text clipping
   - Cramped spacing between nodes
   - Containers not fully enclosing their children
   - Missing or misrouted connections
   - Legend readability and completeness
   - Arrow bends that look wrong despite correct waypoints
   - Color contrast and fill consistency
4. If any visual issues are found, fix them in the XML and repeat from step 1
5. Continue the export→view→fix loop until the diagram is visually clean

**Do NOT skip this step.** Do NOT rely solely on position table analysis. The PNG export + LLM review is the authoritative verification.

---

## Rules

- Only move nodes by the minimum amount needed (typically 5-20px, grid-aligned)
- Never break intentional layout structure (e.g., stacked elements, vertically spread groups)
- When moving a node that has edges with explicit waypoints, update the waypoint coordinates to match
- When moving a node inside a group, update the LOCAL coordinates (relative to group). Edges with `parent="1"` use ABSOLUTE coordinates — recompute to verify
- After all position changes, re-run geometric analysis to confirm all issues are resolved
- When adding waypoints, route through the closest available gap rather than long detours
- For edges between nodes at very different positions (diagonal), add 2 waypoints for the full L-path
- When a waypoint lands exactly on a node boundary, nudge it 10px away
- Prefer center-alignment over left-edge alignment for stacked elements of different widths
- When shortening a container swimlane, verify all source connectors still land within its bounds
- When removing waypoints in favor of hints, verify the auto-router will produce the correct path
- When encountering `container=0` groups, do NOT treat them as coordinate parents — their enclosed nodes use `parent="1"` and absolute coordinates
- When editing edges with `edgeLabel` child cells, preserve the child cell's `parent` reference and relative geometry — do not convert to `value` on the edge or vice versa
- Edge strokeColors must never match any container/block strokeColor in the same diagram — audit for conflicts when creating or inheriting a diagram
- AWS icon labels should use resource names, not service names (the icon shape already identifies the service)
- When edges from external actors (Users, Internet, Vercel) enter a major container (AWS Cloud, VPC), route their vertical segments **outside** the container border with explicit waypoints, staggered 10px apart for parallel edges
- When multiple edges run parallel horizontal segments to the same target region, spread their Y-coordinates at least 15-20px apart to prevent visual stacking
- Prefer exiting toward the target's direction: if the target is left of the source, use `exitX=0` (left side), not `exitX=0.5;exitY=1` (bottom) which creates unnecessary U-detours
- When a fan-out node (ALB) connects to many targets, position it ABOVE and centered over the targets — fan-out edges drop down vertically, avoiding horizontal crossings
- Place all persistent data stores (RDS, caches, search indices) on a unified horizontal band below compute services — never scatter them to different sides of the diagram
- Resize containers to match content width — oversized containers waste space and create unnecessarily long edge routes
- Use proper XML `group` containers for logically related nodes (e.g., external integrations) so they use relative coordinates and move as a unit
- Arrows must enter boxes from LEFT or TOP; exit from RIGHT or BOTTOM — following left-to-right, top-to-bottom reading direction
- Minimum 100px (2 box-sizes) gap between any pair of adjacent nodes — labels and edges need this clearance
- Every L-bend knee must have at least 10px (1 grid square) of straight segment — no zero-length knees
- Apply 3-tier layout (Ingress → Compute → Data) as the default for infrastructure diagrams
