# Draw.io Style Guide

## Shape Conventions

Use consistent shapes by component role:

| Role | Style | Typical size |
|------|-------|-------------|
| Services, APIs, processors | `rounded=1;whiteSpace=wrap;html=1` (rounded rectangle) | 80-100 x 40 |
| Databases, stores, caches | `shape=datastore` (simple) or `shape=cylinder3;backgroundOutline=1;size=10` (detailed) | 70-80 x 60 |
| Algorithms, business logic | `shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1` | 100-300 x 45-55 |
| External data sources | `shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1` | 150-180 x 50 |
| Third-party services | `ellipse;shape=cloud` | 120-150 x 55-65 |
| Containers, groups | `swimlane;fontStyle=1;startSize=25` or `rounded=1;dashed=1;fillColor=none` | varies |
| Visual-only groups | `group;rounded=1;dashed=1;container=0;connectable=0` (boundary box, children stay `parent="1"`) | varies |
| Users, actors | `ellipse;whiteSpace=wrap;html=1;aspect=fixed` (circle) | 40 x 40 |
| Infrastructure (LB, proxy) | `shape=trapezoid` or standard rectangle | 80-100 x 40 |
| Queues, buffers | `rounded=1` with queue-role color (purple), or `shape=mxgraph.flowchart.multi-document` | 70-90 x 40-50 |

**AWS diagrams**: Use the `mxgraph.aws4` shape library extensively — it has hundreds of built-in service icons. Containment hierarchy: AWS Cloud → VPC → Availability Zone → Subnet → Resources. Public subnets: `fillColor=#E9F3E6;strokeColor=#248814` (green). Private subnets: `fillColor=#E6F2F8;strokeColor=#147EBA` (blue). Service-colored arrows: use each service's fill color as strokeColor with `dashed=1;dashPattern=8 8` for managed service integrations.

**AWS standard colors by category**: Purple (#8C4FFF, networking), Orange (#ED7100, compute), Database (#C925D1, Aurora), Green (#7AA116, storage), Security (#DD344C, Secrets Manager), AI (#01A88D, Bedrock).

**AWS icon types** — the library provides two icon patterns:
- **resourceIcon** — Small square (45-50px), colored by category. For individual resources/instances:
  `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{service};fillColor={category_color}`
- **productIcon** — Larger rectangle (80x100), dark fill (#232F3E) with service name integrated. For service-level groupings or prominent callouts:
  `shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.{service};fillColor=#232F3E`

For any AWS service, grep [references/aws4-shapes.txt](aws4-shapes.txt) to find the exact shape name (1032 shapes, Jan 2026), then convert spaces to underscores. Full icon reference with category colors and group shapes: [references/aws4-icons.md](aws4-icons.md).

**Non-AWS stencil libraries**: draw.io ships dozens of stencil libraries beyond AWS4. Common ones:
- `mxgraph.office.*` — Microsoft Office icons (e.g., `mxgraph.office.users.tenant_admin` for admin/team actors)
- `mxgraph.mscae.*` — Microsoft Cloud & AI (e.g., `mxgraph.mscae.intune.user_group` for user group icons)
- `mxgraph.cisco.*`, `mxgraph.azure.*`, `mxgraph.gcp.*` — network/cloud vendor icons
- `mxgraph.flowchart.*` — flowchart shapes (multi-document, decision, etc.)

To discover shape names: open draw.io desktop, search the shape panel, then inspect the XML to extract the exact `shape=mxgraph.*` value. These stencil styles are complex — always copy character-for-character from a working example.

## Color Scheme

Standard fill colors by role (with matching stroke):

| Role | Fill | Stroke | Example |
|------|------|--------|---------|
| Core system components | `#dae8fc` (light blue) | `#6c8ebf` | Services, stores, processors |
| Databases, persistent storage | `#d5e8d4` (light green) | `#82b366` | PostgreSQL, Redis, data stores |
| External-facing / user-facing | `#fff2cc` (light yellow) | `#d6b656` | APIs, apps, dashboards, users |
| External data sources | `#ffe6cc` (light orange) | `#d6b656` | Third-party APIs, SaaS, feeds |
| Algorithms, business logic | `#f8cecc` (light red) | `#b85450` | Scoring engines, state machines |
| Queues, message infrastructure | `#e1d5e7` (light purple) | `#9673a6` | RabbitMQ, buffers, pub/sub |
| Detail panels / neutral | `#f5f5f5` (light gray) | `#666666` | Expanded sub-diagrams, clients |

**Consistency rule**: All elements of the same role must use the same fill/stroke pair. Same fill color = same role.

## Arrow Semantics

Arrows convey connection type through style. Use consistently within a diagram:

| Style | Meaning | Key style attributes |
|-------|---------|---------------------|
| Solid | Synchronous / direct call | `strokeColor=#333333` |
| Dashed | Asynchronous / event-driven | `dashed=1;strokeColor=#333333` |
| Dotted | Scheduled / polling | `dashed=1;dashPattern=1 4` |
| Thick colored | Critical path / latency-sensitive | `strokeColor=#CC0000;strokeWidth=2` |
| Thick green | Training / feedback loop | `strokeColor=#82b366;strokeWidth=2;fontColor=#2d6613` |
| Dashed gray | Offline / backtest / testing path | `dashed=1;strokeColor=#999999` |
| Bidirectional | Two-way communication | `startArrow=classic;endArrow=classic` |
| Reverse | Pull / read direction (arrow at source) | `startArrow=classic;startFill=1;endArrow=none;endFill=0` |
| Gray | Internal / helper | `strokeColor=#666666` or `#999999` |

**Detection**: During Phase 1, catalog all unique edge style combinations. If the diagram uses 3+ distinct arrow styles, it has semantic arrow conventions — preserve them. Do not normalize arrow styles to a single format.

## Label Formatting

Node labels support inline HTML when `html=1` is in the style. Use `<b>Name</b><br>Description<br><i>detail</i>` for multi-line node labels. Use `&#xa;` only for edge labels set via `value` attribute directly on the edge.

**Inline font size overrides**: Use `<font style="font-size: 8px;">` inside cell values for smaller labels in detail panels, while main-flow nodes use the default `fontSize` style attribute (typically 11-12px). This allows mixed font sizes in one diagram without separate style classes.

**Edge labels as child cells**: draw.io's interactive editor creates edge labels as separate `edgeLabel` child cells rather than `value` attributes on the edge:
```xml
<mxCell style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];"
        vertex="1" connectable="0" parent="edge-id">
  <mxGeometry x="0.45" y="-3" relative="1" as="geometry">
    <mxPoint x="4" y="-12" as="offset" />
  </mxGeometry>
</mxCell>
```
The `x` value in geometry is the relative position along the edge (0.0=source, 1.0=target, 0.5=midpoint). The `y` value is perpendicular offset. The nested `<mxPoint as="offset"/>` provides pixel-level fine-tuning. During Phase 1, detect BOTH patterns: `value` on the edge cell AND child `edgeLabel` cells. During cleanup, preserve whichever pattern the diagram uses — do not convert between them.

**Free-standing text cells**: Use `style="text;html=1;..."` with `vertex="1"` for annotations, timing labels, channel descriptions, or diagram titles placed near relevant components. These are not connected by edges.

**Diagram titles**: Use a large free-standing text cell (`font-size: 36px` or similar) at the top-left for the diagram name, with an optional smaller subtitle below (e.g., "Draft", version, date).
