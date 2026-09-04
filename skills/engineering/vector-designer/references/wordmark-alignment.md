# Wordmark & Icon+Text Alignment

Principles learned from Decaf Way logo design (icon + "Decaf Way" text wordmark).

## Optical Centering: Text Next to Icons

**Text must sit slightly ABOVE mathematical center relative to the icon.**

Capital serif letters (especially Playfair Display, Fraunces) are optically bottom-heavy — the bowl of "D", the crossbar of "A", the serifs all add visual weight below the geometric midpoint. When mathematically centered with an icon, the text *feels* like it's sinking.

**Correction**: Place the text center ~8-10 SVG units above the icon's geometric center (in a 500-unit-tall composition). This is the standard optical centering technique used by Google, Airbnb, Spotify wordmarks.

**Example**: Mug center at y=302, text moved from y=206 to y=190 (translate), placing text center at ~293 — about 9 units above mug center.

## What Part of the Icon to Center Against

When an icon has a decorative element that extends beyond its main body (e.g., a location pin above a coffee cup), **center the text against the main body, not the full icon**. The decorative element should naturally protrude above/below the text line.

- Pin+Cup icon: center text against the CUP, let the pin extend above
- Character+Hat icon: center text against the CHARACTER, let the hat extend above
- Building+Antenna icon: center text against the BUILDING

## ViewBox Dead Space

**Unequal padding in the viewBox shifts perceived content position.**

If a viewBox has 25px of content padding at the top but 110px at the bottom, the rendered image appears to float high within its container. When the browser scales the SVG to fit (e.g., `h-10`), the dead space gets scaled too, wasting pixels.

**Fix**: Trim viewBox to tightly frame content bounds + equal small padding. Calculate actual content extent including stroke widths (half extends beyond path coordinates).

**Descender trap**: When trimming, account for letter descenders ('y', 'g', 'p', 'q'). In Playfair Display, the 'y' descender extends ~60 units below the baseline. Always check the lowest point of ALL text paths, not just the baseline.

## Font Selection for Wordmarks (Icon Pairing)

Evaluate fonts on two axes when pairing with an icon:

### 1. Stroke Weight Match
Compare the font's stem thickness to the icon's stroke-width. At the rendered size, they should feel like the same "pen" drew both.

- Too heavy: text overpowers the icon
- Too light: text feels disconnected/fragile
- Test by measuring stem width in pixels at target render size

### 2. Shape Language Harmony
The font's structural character must harmonize with the icon's curves.

| Icon style | Good font match | Bad font match |
|-----------|----------------|---------------|
| Smooth flowing curves (coffee cup, waves) | Flowing serifs (Playfair Display), humanist sans | Blocky slab serifs (Zilla Slab) — 90-degree endings clash |
| Geometric/angular (shield, brackets) | Geometric sans, slab serifs | Ornate/flowing serifs |
| Organic/hand-drawn | Humanist fonts, slightly irregular | Strict geometric fonts |

**Shape language matters more than exact stroke weight.** A font with slightly different weight but matching curves will look more natural than a perfectly weighted font with clashing geometry.

### Tested Fonts (Decaf Way, ranked)

1. **Playfair Display Bold** (winner) — flowing serifs harmonize with smooth cup curves. Slight weight mismatch but best overall feel.
2. **Zilla Slab Medium** — best stroke weight match, but blocky slab-serif endings clash with smooth cup curves.
3. **Zilla Slab SemiBold** — slightly heavy, same shape language clash.
4. **Zilla Slab Bold** — too heavy.
5. **Fraunces 72pt Bold** — high-contrast strokes clash with the cup's uniform stroke-width.

## Text-to-Path Workflow

Reliable pipeline for creating wordmark text paths:

1. Write SVG with `<text>` element using target font
2. Inkscape CLI: `inkscape input.svg --actions="select-all;object-to-path" --export-filename=output.svg`
3. Extract `<path d="...">` from output
4. Embed in wordmark SVG with `transform="translate(x, y)"` for positioning
5. Use `scale()` in transform if original paths need resizing

**Font-size scaling**: If the text-to-path output is too wide/narrow, apply `scale(factor)` in the transform. Calculate factor = target_width / actual_width.

## Wordmark SVG Structure

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H">
  <!-- Icon (group with transform to position/scale) -->
  <g transform="matrix(sx,0,0,sy,tx,ty)" id="icon">
    <!-- icon paths -->
  </g>

  <!-- Word 1 (positioned with translate) -->
  <path transform="translate(x1, y1)" d="..." fill="#1a1a1a" aria-label="Word1"/>

  <!-- Word 2 (positioned with translate) -->
  <path transform="translate(x2, y2)" d="..." fill="#1a1a1a" aria-label="Word2"/>
</svg>
```

- Use `aria-label` on text paths for accessibility
- Keep icon and text as separate top-level elements for independent positioning
- ViewBox should tightly frame all content with equal padding
