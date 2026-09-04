# Design Philosophy: Rams + Swiss Style

This skill follows two named design traditions:

**Dieter Rams — "Weniger, aber besser" (Less, but better).** The most influential product design philosophy in tech. Every rule in this skill traces back to Rams:

| Rams' 10 Principles | Our Rule |
|---|---|
| Good design is **as little design as possible** | Elegance test: "can I remove one element and still communicate?" |
| Good design makes a product **understandable** | One message, perfectly expressed; inner symbol gives identity |
| Good design is **unobtrusive** | Color restraint (one accent), breathing room, neutral structural color |
| Good design is **honest** | No gradients faking depth, no shadows faking dimension |
| Good design is **long-lasting** | "What's out" list — avoid trends that date quickly |
| Good design is **thorough down to the last detail** | Mathematical centering, scale survival testing, equal spacing |
| Good design is **innovative** | Distinctiveness check: "name 3 logos it could be confused with" |

**Swiss International Typographic Style** (Muller-Brockmann, Vignelli). The geometric precision side — grid discipline, limited palette, typography-first. Our "dev tool aesthetic" section is essentially Swiss Style applied to software: integer coordinates, consistent stroke widths, monospace DNA, whitespace as structure.

Together: **Rams tells you what to remove. Swiss Style tells you how to align what's left.**

## Logo Messaging and Tone

### What the Logo Communicates

Before any visual work, identify the **one message** the logo must convey. Every shape, color, and weight choice should reinforce it.

| Message | Shapes that work | Shapes that fail |
|---------|-----------------|-----------------|
| **Security/safety** | Shield, lock, brackets `[ ]` | Open circles, thin lines |
| **Developer tool** | Terminal `>_`, brackets `{ }` `[ ]`, asterisk `*` | Gradients, organic curves |
| **Speed/efficiency** | Chevrons `>>`, lightning, minimal strokes | Heavy/ornate shapes |
| **Isolation/container** | Box, brackets, cell walls | Arrows pointing outward |
| **Code/programming** | Monospace glyphs, brackets, dots | Pictorial/illustrative |

**Layering messages**: A single shape can carry two messages. Brackets `[ ]` = both "code" AND "containment." An asterisk `*` inside brackets = "wildcard/power" inside "safe boundary." The best dev tool logos stack 2 messages in 1-2 shapes — never try to communicate 3+.

### The Dev Tool Aesthetic (what "cool" looks like in 2024-2026)

Dev tools have a distinct visual language. Logos that feel "right" in this space share these traits:

**What's in:**
- **Monospace DNA** — shapes that feel like they belong in a terminal. Brackets, pipes, dots, asterisks. The logo should look at home next to `git status` output.
- **Stroke-first, not fill-first** — outlines with selective accent fill. Feels technical, not corporate. Think: wireframe, not illustration.
- **High contrast + one vivid accent** — `#111` or `#fff` structural elements + one saturated color (burnt orange, neon green, electric blue). Two accent colors = confused brand. Zero = forgettable.
- **Geometric precision** — integer coordinates, consistent stroke widths, deliberate spacing. Pixel-perfect at small sizes. Hand-drawn or organic curves feel wrong in this space.
- **Dark-mode-first design** — the dark variant should be the hero. Neon accent on `#111` background is the canonical dev tool look. If the logo only looks good on white, it's not a dev tool logo.
- **Typographic integration** — logo icon + wordmark should feel like one unit. Monospace font, tight letterspacing, icon sized to match cap height. The animation pattern (icon → expands to full wordmark) reinforces this unity.
- **Breathing room** — generous whitespace inside and around the mark. Crowded logos feel enterprise, not dev tool.

**What's out:**
- Gradients (feel 2015, not 2025)
- 3D/drop shadows (skeuomorphic, dated)
- Rounded-everything / "friendly" blob shapes (consumer app, not dev tool)
- Complex illustrations or mascots at logo scale (save for docs/marketing)
- Multiple accent colors (confused identity)
- Thin hairline strokes everywhere (disappear at small sizes, feel fragile)
- Symmetry for symmetry's sake (slight asymmetry — like an offset dot — adds character)

### Reference Logos That Nail It

Study these for calibration (not copying):
- **Vercel** — triangle. One shape, one concept (deploy/forward), works at any size
- **Linear** — overlapping lines. Feels like a UI but isn't. Geometric precision.
- **Warp** — stylized `>`. Terminal DNA, one vivid accent, dark-first.
- **Raycast** — angled rays. Minimal strokes, strong silhouette, monochrome works.
- **Fig/Amazon Q** — `>_` terminal prompt. Direct domain reference, unmistakable.

**Common thread**: minimal element count (1-3), terminal/code visual language, geometric precision, one accent color, looks best on dark.

### Elegance Through Restraint

The difference between a good logo and a great one is what you *remove*, not what you add.

**The elegance test** — after each iteration, ask: "Can I remove one element and still communicate the same message?" If yes, remove it. Repeat until you can't.

**Principles of elegant marks:**
- **One idea, perfectly expressed.** A bracket pair `[ ]` with a single asterisk inside is more elegant than a bracket pair with an asterisk, a dot, a cursor, AND a highlight. Each additional element dilutes the message.
- **Negative space does work.** The space *between* brackets IS the "containment" message. You don't need to fill it with a box shape to communicate "container." Trust the viewer.
- **Weight variation creates sophistication.** A logo with 2-3 deliberate stroke weights (thick boundary, medium symbol, thin detail) reads as designed. Uniform weight reads as default/lazy.
- **Color restraint = confidence.** One accent color says "I know who I am." Multiple colors say "I'm trying too hard." Gray/muted details are elegant because they support without competing.
- **Asymmetry with purpose.** A perfectly centered, perfectly symmetric mark feels sterile. One deliberate asymmetry (an offset dot, a slightly different bracket weight) adds personality. But it must be *deliberate* — random asymmetry looks broken.

**Signs a logo is overloaded:**
- More than 6 SVG elements (paths, lines, circles)
- More than 2 colors besides black/white
- You need to explain what elements represent
- Details disappear at 32px
- The mark doesn't work in monochrome

**Signs a logo is elegant:**
- You can describe it in one sentence ("brackets with an asterisk and a dot")
- It looks intentional at every size
- Removing any element would break the concept
- It works in monochrome, with accent, AND animated
- Someone could sketch it from memory after seeing it once
