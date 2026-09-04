# Phase 5: Design System Extraction

Extracts visual tokens and design patterns from source code and live screenshots. Produces `design-system.md`. Independently runnable — does not require Phases 1–4 to have completed first.

**Primary scan targets:**
```
src/constants/theme.ts          ← canonical token source (colors, spacing, typography, animations)
src/constants/designSystem.ts   ← product-specific scale (dopamine tokens, layout constants)
src/constants/colors.ts         ← standalone color file (if theme.ts delegates)
styles/*.ts                     ← stylesheet constants
src/components/*.tsx            ← component anatomy (card, badge, button, loading, empty states)
screenshots/                    ← Playwright captures from 5.0 (referenced in 5.6, 5.7)
```

---

## Progress Checklist

```
Phase 5: DESIGN SYSTEM EXTRACTION Progress:
- [ ] 5.0: Visual capture (Playwright screenshots of all screens)
- [ ] 5.1: Color palette extraction
- [ ] 5.2: Typography extraction
- [ ] 5.3: Spacing & layout extraction
- [ ] 5.4: Component pattern extraction
- [ ] 5.5: Animation extraction
- [ ] 5.6: Screen layout descriptions (source + screenshots)
- [ ] 5.7: Image & icon asset inventory (source + screenshots)
- [ ] 5.8: Brand voice extraction
- [ ] 5.9: Generate design-system.md
```

---

## 5.0: Visual Capture (Playwright MCP)

Capture screenshots of every reachable screen before source-code extraction. Screenshots ground the design system in what users actually see — not just what the code declares.

**Prerequisite:** App must be running locally (see Phase 0). Playwright MCP must be available.

**Process:**

1. Navigate to the app root URL (`localhost:[port]`)
2. For each tab in the main tab bar: click the tab, then capture
3. For each screen: **perform a full scroll to the bottom before capturing** — including any inner scroll containers (nested `ScrollView`, horizontal sliders, `FlatList` children)
4. Take screenshot with `browser_take_screenshot` — use `fullPage: true` when possible
5. Save each screenshot to `screenshots/[screen-name].png` in the project directory
6. Navigate to modals, sheets, and secondary screens by triggering the actions that open them — screenshot each

**Scroll protocol (apply to EVERY screen):**
```
1. browser_navigate → [screen URL or tab click]
2. browser_wait_for time=1        ← wait for initial load + animations
3. browser_run_code:
     async (page) => {
       // Scroll main page
       await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
       // Scroll all inner scroll containers
       await page.evaluate(() => {
         document.querySelectorAll('*').forEach(el => {
           if (el.scrollHeight > el.clientHeight && el.clientHeight > 0) {
             el.scrollTop = el.scrollHeight;
           }
         });
       });
       await new Promise(r => setTimeout(r, 500));
     }
4. browser_take_screenshot fullPage=true → screenshots/[name].png
```

**Screen capture order:**
1. Auth screens (welcome, login, register)
2. Main tab screens (in tab bar order)
3. Tool screens (by category group)
4. Settings screens
5. Modal / bottom sheet screens (trigger and capture each)
6. Education and social screens

**Output:** `screenshots/` directory with one PNG per screen. Create `screenshots/index.md` listing each file and its screen name/route.

**Quality check:**
- [ ] Every main tab screen captured
- [ ] At least one tool screen per category captured
- [ ] Modals and bottom sheets captured in open state
- [ ] Full-page screenshots (no content cut off at viewport bottom)
- [ ] Inner scroll containers scrolled to reveal full content before capture
- [ ] `screenshots/index.md` created

---

## 5.1: Color Extraction

**Source files to scan:**
- `src/constants/theme.ts`, `src/constants/colors.ts`, `src/constants/designSystem.ts`
- Grep `#[0-9A-Fa-f]{6}` and `rgba\(` across `src/` and `styles/`
- Grep `colors\.` or `theme\.colors` usages in screen/component files for semantic role mapping

**Process:**
1. Read `theme.ts` (or `constants/colors.ts`) → collect all named color definitions
2. Identify structure: flat object vs nested (dark theme / light theme)
3. Grep for `rgba(` and alpha-append patterns (`color + '20'`, `+ '15'`, `+ 'AA'`) → identify opacity tinting conventions
4. Grep across screen/component files for `backgroundColor`, `color`, `borderColor` → map token names to visual roles
5. Identify semantic groups: backgrounds (depth stack), brand colors, semantic trio (success/warning/danger), text hierarchy, border tokens, result-specific colors, interaction-state colors
6. Note light/dark theme variants and which is default

**Output template:**
```markdown
## Color Palette

### [Primary Theme] (Default)

**Backgrounds ([N]-depth stack):**
| Token | Hex | Use |
|-------|-----|-----|
| [name] | `[hex]` | [role] |

**Brand:**
| Token | Hex | Use |
|-------|-----|-----|

**Semantic:**
| Token | Hex | Use |
|-------|-----|-----|

**Text:**
| Token | Hex | Use |
|-------|-----|-----|

**Borders:**
| Token | Hex | Use |
|-------|-----|-----|

**Alpha Tinting Convention:**
`[color token] + '[hex suffix]'` → [opacity]% opacity (e.g., `success + '20'` = 12% opacity background)

### [Alternate Theme] (if present)
[Same table structure, noting only tokens that differ from primary theme]
```

**Quality check:**
- [ ] All named color tokens from theme.ts documented
- [ ] At least 5 semantic groups identified (backgrounds, brand, semantic, text, borders)
- [ ] Alpha tinting convention documented if present
- [ ] Light and dark theme variants noted

---

## 5.2: Typography Extraction

**Source files to scan:**
- `src/constants/theme.ts` → base type scale
- `src/constants/designSystem.ts` → product-specific typography (dopamine scale, stat labels)
- Grep `fontSize`, `fontWeight`, `letterSpacing`, `lineHeight` across `src/components/` and `app/(tabs)/`
- Grep `fontFamily` → identify font strategy (system fonts vs custom)

**Process:**
1. Read theme.ts → collect all named text styles (h1, h2, body, caption, etc.)
2. Collect: size (px), weight (numeric or string), letter spacing, line height, use context
3. Read designSystem.ts → collect additional product-specific scales (hero stats, dopamine numbers, etc.)
4. Grep for `fontFamily` → identify whether system fonts are used or custom fonts loaded
5. Check `app.json` or `assets/fonts/` for custom font assets
6. Note any ALL_CAPS or text transform conventions
7. Merge duplicates — prefer theme.ts as canonical source

**Output template:**
```markdown
## Typography

### Scale ([source: theme.ts])
| Style | Size | Weight | Spacing | Use |
|-------|------|--------|---------|-----|
| h1 | [px] | [weight] | [value or —] | [role] |

### [Additional Scale] ([source: designSystem.ts])
| Style | Size | Weight | Spacing | Use |
|-------|------|--------|---------|-----|

### Font Family
- **Strategy:** [System fonts only / Custom: [font name]]
- **iOS:** [font name]
- **Android:** [font name]
- **Custom assets:** [path or "none"]
```

**Quality check:**
- [ ] All named text styles documented with size, weight, spacing
- [ ] Font family strategy confirmed (system vs custom)
- [ ] Both base scale and product-specific scales captured

---

## 5.3: Spacing & Layout Extraction

**Source files to scan:**
- `src/constants/theme.ts` → spacing scale, border radius tokens
- `src/constants/designSystem.ts` → layout constants (screen padding, card dimensions)
- Grep `padding`, `margin`, `gap`, `borderRadius` in `src/components/*.tsx` → usage patterns
- Grep `Platform.OS` → iOS/Android differences (tab bar heights, safe area)

**Process:**
1. Read theme.ts → collect all named spacing tokens (xs, sm, md, lg, xl, etc.) with px values
2. Read theme.ts/designSystem.ts → collect border radius tokens
3. Grep layout constants → horizontal padding, card gutter, max content width
4. Read `src/components/` card components → extract card anatomy (padding, border, background, radius)
5. Note Platform-specific values (iOS tab bar vs Android)

**Output template:**
```markdown
## Spacing

| Token | Value | Use |
|-------|-------|-----|
| xs | [px] | [role] |

### Layout Constants
| Constant | Value | Use |
|----------|-------|-----|

## Border Radius
| Token | Value | Use |
|-------|-------|-----|

## Card Patterns

### [Variant Name]
```
backgroundColor:  [token] ([hex])
borderRadius:     [value]
borderWidth:      [value]
borderColor:      [token] ([hex])
padding:          [value]
[any other properties]
```

## Tab Bar
| Platform | Height |
|----------|--------|
| iOS | [px] |
| Android | [px] |
```

**Quality check:**
- [ ] Complete spacing scale from smallest to largest token documented
- [ ] Border radius scale documented
- [ ] At least 2 card variants with full anatomy
- [ ] Tab bar heights for both platforms

---

## 5.4: Component Pattern Extraction

**Source files to scan:**
- `src/components/*.tsx` — all shared component files
- `app/(tabs)/*.tsx` — tab screens for badge, button, segmented control usage
- Grep `StyleSheet.create` across component files → extract style objects directly

**Process:**
1. Read badge/tag components → extract each variant: background color, text color, border radius, padding, font size/weight
2. Read button components → extract each variant: background, text, border radius, padding, height, active/disabled states
3. Read segmented control or tab toggle → extract inactive/active states
4. Read loading state components (shimmer, skeleton, spinner) → document visual pattern and animation
5. Read empty state components → document anatomy (icon/emoji, title, body, CTA)
6. Note alpha tinting pattern on badge backgrounds (`successColor + '20'` etc.)

**Output template:**
```markdown
## Badge / Tag Patterns

### [Badge Type]
```
backgroundColor:  [token + alpha] (e.g., success + '20' → green at 12% opacity)
textColor:        [token]
borderRadius:     [value] (pill / [px])
paddingH:         [value]
paddingV:         [value]
fontSize:         [value]
fontWeight:       [value]
```

## Button Patterns

### [Button Type]
```
backgroundColor:  [token or gradient]
textColor:        [token]
borderRadius:     [value]
padding:          [value]
height:           [value]
[disabled state differences]
```

## Segmented Control / Toggle
### Inactive
[token values]
### Active
[token values]

## Loading States

### [Shimmer/Pulse/Spinner]
[Visual description + animation details]

## Empty States
**Anatomy:** [emoji/icon] → [title] → [supporting text] → [CTA button]
**Background:** [card or screen background]
```

**Quality check:**
- [ ] All badge color variants documented with alpha tinting convention noted
- [ ] Primary and secondary button variants extracted
- [ ] Loading state pattern documented (shimmer animation details)
- [ ] Empty state anatomy documented

---

## 5.5: Animation Extraction

**Source files to scan:**
- `src/constants/theme.ts` → animation presets (spring configs, duration constants)
- Grep `useSharedValue`, `withSpring`, `withTiming` in `src/components/` and `app/` → usage patterns
- Grep `Haptics.` → haptic feedback triggers
- `package.json` → confirm animation library (react-native-reanimated vs Animated)

**Process:**
1. Read theme.ts → collect all named spring presets: damping, stiffness, mass, overshootClamping
2. Collect duration constants: fast, normal, slow (ms values)
3. Grep `withSpring` usage in components → identify which spring preset is used per interaction
4. Grep `Haptics.` → document: which action triggers haptics, what type (impact/notification/selection), what intensity
5. Read package.json → confirm reanimated vs Animated.* and version

**Output template:**
```markdown
## Animations

### Spring Presets
| Preset | Damping | Stiffness | Mass | Use |
|--------|---------|-----------|------|-----|

### Duration Constants
| Name | Value | Use |
|------|-------|-----|

## Haptic Feedback
| Trigger | Type | Intensity |
|---------|------|-----------|

## Animation Library
[react-native-reanimated / RN Animated — confirmed from package.json]
```

**Quality check:**
- [ ] All unique spring configs documented with named presets
- [ ] All unique duration constants documented
- [ ] Haptic feedback triggers and intensities documented
- [ ] Animation library confirmed from package.json

---

## 5.6: Screen Layout Descriptions

**Source files to scan:**
- Cross-reference Phase 1 screen inventory + Phase 2 feature list
- Read top 8–10 screens by feature count (main tabs first, then most-used tool screens)
- Focus on `app/(tabs)/*.tsx` and `app/(tools)/*.tsx`
- **Also read screenshots from `screenshots/`** — use `Read` tool on each PNG to visually verify layout against source code

**Process:**
1. For each main tab screen: read the source file AND open its screenshot from `screenshots/`
2. Identify the layout skeleton from both sources: what renders first, second, third?
3. Classify screen type:
   - `dashboard`: hero metric → content sliders → main list
   - `list`: filter bar → scrollable card list with tier accents
   - `detail`: full-width hero → stats row → action buttons
   - `calculator`: form inputs → compute button → result display
   - `chat`: message thread (FlatList inverted) → text input
   - `hub`: pipeline/grid of tool cards
   - `gamified`: XP bar → progress → content grid
4. Use screenshots to verify: does visual rendering match code structure? Note discrepancies
5. Document content hierarchy order (top → bottom) — screenshot = source of truth for visual order, source code = slot names
6. Note sticky elements visible in screenshots (fixed headers, persistent filter bars)
7. Note horizontal scroll patterns visible in screenshots (card sliders — how many cards visible? gap size?)
8. Characterize information density: minimal / medium / high

**Output template:**
```markdown
## Screen Layout Patterns

### [Pattern Name] — ([example screens])

**Layout skeleton (top → bottom):**
1. [element]
2. [element]
…

**Key characteristics:**
- Density: [minimal/medium/high]
- Scroll: [vertical / horizontal sliders / paginated / hybrid]
- Sticky elements: [list]
- [Notable pattern: e.g., "tier-accented left border on every card"]
```

**Quality check:**
- [ ] All distinct layout archetypes identified (not every screen — just patterns)
- [ ] Every tab screen mapped to an archetype
- [ ] Information density characterized per pattern

---

## 5.7: Image & Icon Asset Inventory

**Source files to scan:**
- Grep `from '@expo/vector-icons'` or `from 'react-native-vector-icons'` → icon library
- Grep `<Ionicons`, `<MaterialIcons`, `<Feather`, `<FontAwesome` → icon component usage
- Glob `assets/images/**`, `assets/icons/**`, `assets/**/*.{png,svg,jpg}`
- Grep `require('./assets/` → referenced asset filenames
- Grep emoji literals in screen files → emoji-as-icon usage pattern
- **Also read screenshots from `screenshots/`** → visually identify rendered icons, image assets, and empty state illustrations

**Process:**
1. Read `package.json` → identify icon library package(s) and version
2. Grep icon component usage → collect unique icon names and their `size=` prop values
3. Deduplicate icon sizes → identify sizing conventions per context (tab bar, card, button, header)
4. Grep for active vs inactive icon color props → document color convention
5. Glob `assets/` directories → list subdirectories and file count by type
6. Grep for emoji in JSX text nodes (`"🏆"`, `"⚡"`, etc.) → identify emoji-as-icon usage
7. Read screenshots → visually confirm actual rendered icons and image assets; note any assets visible in screenshots but not caught by source grep

**Output template:**
```markdown
## Icon System

**Library:** [@expo/vector-icons — Ionicons / MaterialIcons / etc.]
**Sets used:** [list]

**Size conventions:**
| Context | Size |
|---------|------|

**Color conventions:**
| State | Color |
|-------|-------|

---

## Image Assets
| Directory | Contents |
|-----------|----------|

**Emoji as icons:** [Yes/No — usage: "empty states (64px), achievement badges, decorative"]
```

**Quality check:**
- [ ] Icon library identified from package.json
- [ ] Icon size conventions documented (tab bar, card header, inline)
- [ ] Active/inactive icon color convention documented
- [ ] Assets directories inventoried (or noted as empty/minimal)

---

## 5.8: Brand Voice Extraction

**Source files to scan:**
- Grep string literals in `app/(tabs)/*.tsx` → screen titles, subtitles, section headers, CTA text, empty state copy
- Grep `"No "`, `"Get started"`, `"Try "`, `"You haven't"` in screen files → empty state language
- `src/utils/` → number formatting functions (formatCurrency, formatPercent, formatRatio, formatScore, etc.)
- `src/constants/` → any copy constants, copy strings, or i18n files

**Process:**
1. Collect screen titles from `navigation.setOptions({ title: })` and top-level `<Text>` headings → note capitalization convention (Title Case / UPPER CASE / Sentence case)
2. Collect CTA button labels → note verb choice, tone (imperative? confident? cautious?)
3. Read number formatting utility functions → document format per data type: how are currencies, percentages, ratios, scores, rankings displayed?
4. Collect 3–5 empty state instances: emoji/icon, title, message body, CTA label → document anatomy and copy tone
5. Note loading state language (do loading skeletons show any text, or just visual placeholders?)
6. Identify tone markers: aggressive/confident/expert, neutral/functional, or warm/encouraging?

**Output template:**
```markdown
## Brand Voice

### Tone
[2–3 sentences describing personality. Confident? Expert? Encouraging? Action-oriented?]

### Header Style
[Capitalization convention with examples from actual screens.]

### Number Presentation
| Data Type | Format | Example |
|-----------|--------|---------|
| [type] | [format description] | `[example]` |

### Empty State Language
**Pattern:** [icon/emoji] → [title] → [supporting message] → [CTA button]
**Tone:** [description]
**Examples (from screens):**
- [Screen name]: "[title]" / "[CTA label]"

### Loading State Language
[Shimmer/skeleton only (no text) / spinner with label / etc.]

### CTA Language Patterns
[Verb choices. Examples. Imperative vs invitational tone.]
```

**Quality check:**
- [ ] Capitalization convention documented with real screen examples
- [ ] All distinct numeric data types have documented format patterns
- [ ] Empty state pattern documented (icon + text + CTA anatomy)
- [ ] Tone description captures personality, not just formatting rules

---

## 5.9: Generate design-system.md

Assemble all sections from 5.1–5.8 into a single `design-system.md`.

**Assembly order:**
1. Title + Philosophy (synthesize from brand voice §Tone + overall design evidence)
2. Color Palette (from 5.1)
3. Typography (from 5.2)
4. Spacing (from 5.3)
5. Border Radius (from 5.3)
6. Card Patterns (from 5.4 + 5.3)
7. Badge / Tag Patterns (from 5.4)
8. Button Patterns (from 5.4)
9. Segmented Control / Toggle (from 5.4)
10. Tab Bar (from 5.3)
11. Loading States (from 5.4 + 5.5)
12. Empty States (from 5.4)
13. Animations (from 5.5)
14. Haptic Feedback (from 5.5)
15. Gradients (from 5.1, if gradient tokens exist)
16. Number Formatting (from 5.8)
17. Brand Voice (from 5.8)
18. Screen Layout Patterns (from 5.6)
19. Icon System + Image Assets (from 5.7)

**Philosophy section format:**
```markdown
## Philosophy

**"[tagline or design philosophy quote]"** — [one-line description].
[Theme preference (dark-first/light-first)]. [Information density approach]. [Font strategy].
```

Write the Philosophy by answering: What emotional experience does this UI optimize for? What does every design decision serve?

**Output:** Save as `design-system.md` in the project root alongside `features.md`.

---

## Design System Quality Checklist

- [ ] `design-system.md` generated and saved to project root
- [ ] Color tokens: ≥5 semantic groups (backgrounds, brand, semantic, text, borders)
- [ ] Typography: all named text styles documented with size + weight + spacing
- [ ] Spacing: complete scale from xs to largest named token
- [ ] At least 2 card variants documented with full anatomy
- [ ] At least 1 loading state pattern documented
- [ ] Empty state anatomy documented (icon + title + body + CTA)
- [ ] Animation presets documented (spring configs + duration constants)
- [ ] Brand voice captures tone + number formatting conventions
- [ ] All token names match source code exactly (copy-paste safe)
- [ ] Philosophy section captures emotional/design intent, not just technical tokens
