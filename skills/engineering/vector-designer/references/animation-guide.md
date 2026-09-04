# Logo Animation (CSS)

## Brand Reveal Pattern

The most effective logo animation for dev tools: **compressed wordmark → expands to full name on page load**. Example: `[*.]cell` holds → gap opens → `dev` fades in → `[*.] dev cell`.

## Architecture

Animation lives in **CSS on HTML wrapper elements**, NOT inside the SVG. The SVG icon stays rigid and unchanged. This means:

1. **SVG must be inline** (not `<img>` tag) — enables parent CSS to control SVG elements (e.g., bracket color for dark mode)
2. **HTML structure** wraps the SVG + text spans with animation containers
3. **HTML comments** (`<!-- -->`) between inline elements prevent whitespace gaps in `inline-flex`

## HTML Structure

```html
<a class="logo"><!--
  --><svg class="logo-icon" viewBox="0 0 64 64"><!-- inline SVG --></svg><!--
  --><span class="logo-spacer"></span><!--
  --><span class="logo-reveal"><span class="logo-reveal-text">dev</span></span><!--
  --><span class="logo-accent">cell</span>
</a>
```

## CSS Animation Pattern

Three coordinated animations with staggered delays:

```css
/* Container: inline-flex, icon is flex-shrink: 0 (rigid) */
.logo { display: inline-flex; align-items: center; }
.logo-icon { flex-shrink: 0; width: 1.6em; height: 1.6em; }

/* 1. Spacer: opens gap between icon and text */
.logo-spacer {
  display: inline-block; width: 0; flex-shrink: 0;
  animation: spacer-open 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.4s forwards;
}

/* 2. Reveal container: expands to fit hidden text */
.logo-reveal {
  display: inline-block; max-width: 0; overflow: hidden;
  white-space: nowrap; margin-right: 0.25em;
  animation: gap-open 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.4s forwards;
}

/* 3. Text: fades in after container opens */
.logo-reveal-text {
  opacity: 0;
  animation: text-fade 0.3s ease-out 0.7s forwards;
}

@keyframes spacer-open { to { width: 0.25em; } }
@keyframes gap-open    { to { max-width: 4ch; } }
@keyframes text-fade   { to { opacity: 1; } }
```

## Timing Sequence

| Phase | Delay | Duration | What happens |
|-------|-------|----------|--------------|
| Hold | 0s | 0.4s | Logo shows as `[*.]cell` — user registers the mark |
| Expand | 0.4s | 0.6s | Spacer + reveal container open simultaneously |
| Fade | 0.7s | 0.3s | Hidden text fades to full opacity |
| Rest | 1.0s+ | forever | Final state: `[*.] dev cell` (CSS `forwards` fill mode) |

**Key constraints:**
- Icon (`[*.]`) NEVER changes size — `flex-shrink: 0`
- Spacing between icon↔text and text↔accent must be equal (both 0.25em)
- `forwards` fill mode is critical — animation must persist in final state
- `cubic-bezier(0.4, 0, 0.2, 1)` (Material ease-out) gives natural deceleration

## Dark Mode for Animated Logos

Since the SVG is inline, parent CSS controls element colors directly:

```css
/* Light mode default */
.logo-icon .bracket { stroke: #111; }
/* Dark mode override */
.dark .logo-icon .bracket { stroke: #fff; }
```

This is more reliable than `@media (prefers-color-scheme: dark)` inside the SVG, because:
- Works with class-based theme toggles (`.dark` on body)
- Parent CSS specificity always wins over SVG internal styles
- No dependency on OS-level dark mode detection

## Replay (for testing)

Clone-and-replace restarts CSS animations without page reload:

```js
function replay() {
  document.querySelectorAll('.logo').forEach(el => {
    el.parentNode.replaceChild(el.cloneNode(true), el);
  });
}
```

## Build a Standalone Test Page First

Always create `logo-animation-test.html` before integrating into a framework:
- Test light, dark, and multiple sizes in one page
- Iterate timing without framework rebuild cycles
- Only port to framework (Astro, React, etc.) after animation is finalized

## Dark Mode SVG — Delivery Methods

| Method | Dark mode works? | CSS control? | Use case |
|--------|-----------------|--------------|----------|
| `<img src="logo.svg">` | NO (media query ignored) | NO | Static assets only, no dark mode needed |
| `<link rel="icon" href="favicon.svg">` | YES (media query works) | NO | Favicons — use `@media` inside SVG `<style>` |
| Inline `<svg>` in HTML | YES (parent CSS) | YES | Headers, animated logos, themed components |
| `background-image: url(logo.svg)` | NO | NO | Avoid for logos |

**Rule:** If the logo needs dark mode or animation, inline it. If it's a favicon, use SVG with internal `@media` CSS. Never use `<img>` for dark-mode logos.
