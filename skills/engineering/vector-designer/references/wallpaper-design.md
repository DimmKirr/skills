# Wallpaper & Landscape Design

## When Logo Rules Don't Apply

Wallpapers/backgrounds are the opposite of logos in key ways:

| Logo rule | Wallpaper reality |
|-----------|-------------------|
| No gradients | Gradients are essential — they create depth and light |
| 2-4 elements max | 10-15 layered paths are normal |
| One accent color | Full spectrum transitions work (blue→teal→green→lime) |
| Stroke-first | Fill-first — solid colored shapes, no outlines |
| Geometric precision | Organic cubic bezier curves, flowing forms |

## Anatomy of a macOS-Style Wave Wallpaper

**Layer structure** (back to front):
1. **Background rect** — darkest color, full canvas, sets the mood
2. **Wave bands** (5-7) — each a `<path>` with cubic beziers for top edge, straight/curved bottom closing back to fill. Color progression from cool (blues) through accent (teal, green, lime)
3. **Echo/transition waves** (2-3) — semi-transparent (`opacity: 0.65-0.7`) to smooth color jumps between the accent band and the dark bottom
4. **Bottom layers** (2-3) — progressively darker navy fills, each with a wave top edge, extending to below the viewBox
5. **Centered element** (logo/mark) — small relative to canvas, with glow filter for visibility

**Wave path pattern:**
```
M-100,Y1 C cp1 cp2 cp3 C cp4 cp5 cp6 ... L3940,Y2 L3940,2260 L-100,2260 Z
```
- Extend paths beyond viewBox edges (`-100` left, `3940` right) to avoid visible wave endpoints
- Top wave extends above viewBox (`y=-200`) to bleed into the top edge seamlessly
- Bottom layers extend below viewBox (`y=2260`) to prevent gaps

## Color Progression Strategy

**Don't pick individual wave colors — design the full gradient progression upfront:**

```
Dark blue → Medium blue → Bright blue → Teal → Green → Accent (lime) → Teal echo → Blue echo → Medium navy → Dark navy
```

Each wave's gradient should flow in the same direction (diagonal, following the wave movement). This creates a unified "light source" feel.

**Key learning: the accent band is the hardest part.** If the brand accent is highly saturated (like `#C8FF00` lime), it will scream against the surrounding blues/greens. Solutions:
- **Perpendicular gradient** (`x1=0 y1=0 x2=0 y2=1` with `gradientUnits="objectBoundingBox"`) — dark edges, bright center creates a 3D tube/ribbon effect that contains the brightness
- **Narrow the band** — thinner accent stripe = less visual weight
- **Transition waves** — add semi-transparent echo waves above and below the accent to smooth the color jump

## Saturated Brand Colors in Compositions

Colors like `#C8FF00`, `#FF0000`, `#00FFFF` are designed for small UI accents (buttons, links). At wallpaper scale they overpower everything.

**Taming strategies:**
1. **Perpendicular gradient** — the most effective technique. Gradient runs top-to-bottom within the wave band (not along it), with darker versions of the color at edges (`#5a9018`) and the pure accent only in a narrow center strip (`42%-58%`)
2. **Reduce the area** — make the accent band physically thinner than surrounding waves
3. **Surround with complementary transition colors** — green → lime → green feels natural; blue → lime → blue feels jarring
4. **Never use the raw color as a flat fill** — always gradient it

## Logo Visibility on Dark Backgrounds

When placing a logo on a dark/busy wallpaper background:
- **White structural elements** (`#ffffff`) with subtle opacity (`0.95`) for brackets
- **Warm glow filter** on the accent element (e.g., orange asterisk):
  ```xml
  <filter id="warmglow" x="-2" y="-2" width="5" height="5">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feFlood flood-color="#E85D26" flood-opacity="0.4" result="color"/>
    <feComposite in="color" in2="blur" operator="in" result="glow"/>
    <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  ```
- **Enlarge subtle details** — a dot that's `r=4` in a 64px logo should be `r=4.5` when scaled on a busy background
- **Brighten grays** — `#AAAAAA` → `#C0C8D0` (slightly blue-tinted to match the palette)

## Wallpaper Iteration Pattern

Wallpapers converge differently than logos:

| Phase | Iterations | Focus |
|-------|-----------|-------|
| v1-v3 | Wave shape & curvature | Get the fabric-fold feel right |
| v4-v6 | Spacing & density | Gaps between waves, number of bottom layers |
| v7-v10 | Color balance | Accent brightness, bottom darkness, top blending |
| v11-v13 | Polish | Filters, echo waves, transition smoothing |
| v14-v17 | Brand integration | Logo colors, accent color matching, fine-tuning |

**Key insight: color balance dominates the second half of iteration.** Wave shapes stabilize by v5, but color takes 10+ rounds because each change affects the entire composition. Plan for this.

## Wallpaper Self-Assessment Checklist

1. **Top edge**: Does the first wave blend seamlessly into the top? No background color gap visible?
2. **Bottom depth**: Are there 2-3 distinct navy layers, not a flat dark block?
3. **Accent containment**: Is the brightest band narrow enough to not overpower?
4. **Transition smoothness**: Do echo/transition waves bridge the accent-to-dark jump?
5. **Wave character**: Do the curves feel organic/fabric-like, not mathematical/sinusoidal?
6. **Logo legibility**: Can you read every logo element clearly against the background?
7. **No dark colors below navy**: The darkest color should be navy blue (`#081c50`), never near-black (`#030816`)

## Design Process Learnings (from practice)

### Always Read Source-of-Truth Files for Colors

**Never assume colors from memory or context.** Before any design work:
- Read the actual logo SVG for exact stroke/fill colors
- Read CSS/layout files for accent colors, CSS variables
- Cross-reference: the logo's accent color may differ from the site's accent color (e.g., logo asterisk = `#E85D26` burnt orange, site accent = `#C8FF00` lime)

Getting colors wrong wastes 3-5 iterations. Reading files takes seconds.

### What Helps Find the Right Approach Faster

1. **Ask about existing visual assets early** — reference wallpapers, logos, color palettes. The user's existing assets contain implicit design constraints that save massive iteration.
2. **Design the full color progression before coding any SVG** — sketch the gradient spectrum (background → accent → bottom) as a sequence of hex values. This prevents the "one wave looks good but the whole thing clashes" problem.
3. **Start with solid fills, add complexity later** — opacity, filters, and shadows are polish. Get the base composition and colors right with flat fills first. Adding smokiness/blur early makes it harder to evaluate color balance.
4. **Perpendicular gradients for accent bands** — this should be the default for any highly saturated accent color in a landscape composition. It's the fastest path to a controlled, professional look.
5. **Treat "make it more professional" feedback as: add depth layers + smooth transitions** — the difference between amateur and pro wallpapers is usually: (a) more gradient layers in the bottom half, (b) echo waves bridging color jumps, (c) no flat-colored sections.
