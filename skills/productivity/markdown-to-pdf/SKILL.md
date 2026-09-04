---
name: markdown-to-pdf
description: >
  Convert markdown to PDF, create PDF from .md file, render markdown as print-ready document.
  Use when: "convert markdown to pdf", "create pdf out of this file", "render this as pdf",
  "make a pdf from markdown", or any request to turn a .md file into a styled PDF document.
---

# Markdown → PDF

Convert any `.md` file to a styled A4 PDF using `render.py` + `template.html`. No build system, no browser.

**Stack:** Python `markdown` → HTML → WeasyPrint (native PDF, proper text selection)
**Fonts:** System sans-serif (body) + Georgia/serif (headings) + Courier New/monospace (code)

## When NOT to use

- Creating markdown content from scratch (write the .md first, then convert)
- HTML or web page generation (not a web publishing tool)
- Slide decks or presentations
- Spreadsheet or data exports

## Usage

```bash
python3 /path/to/skill/render.py input.md output.pdf [flags]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--title` | First H1 in file | Document title (cover + `<title>`) |
| `--subtitle` | empty | Monospace label above title on cover |
| `--date` | empty | Date shown in cover meta |
| `--org` | empty | Organization shown in cover meta |
| `--dark` | off | Dark gradient cover (default: light) |
| `--cover` | off | Show cover page |

**Examples:**
```bash
# Minimal — title extracted from first H1
python3 render.py README.md readme.pdf

# With cover page
python3 render.py spec.md spec.pdf --cover --title "API Spec" --subtitle "Engineering" --date "March 2026" --org "Acme Corp" --dark
```

**Dependencies:**
```bash
pip install markdown weasyprint
```

## Template Design

The template uses a **Tufte-influenced heading hierarchy** with system fonts:

| Level | Font | Size | Role |
|-------|------|------|------|
| H1 | Georgia/serif | 20pt | Document/chapter title, ink bottom border |
| H2 | System sans uppercase | 7.5pt | Structural section label (muted, wide-tracked) |
| H3 | Georgia/serif | 11pt | Content heading (the actual readable heading) |
| H4 | System sans italic | 9pt | Sub-heading |
| Body | System sans | 9.5pt | Body text, 1.6 line-height |
| Code | Courier New/monospace | 7.5pt | Inline and block code |

**Key design decisions:**
- H2 recedes as a section divider; H3 is the content headline (McKinsey/Bloomberg convention)
- Tables use `font-variant-numeric: tabular-nums` for aligned number columns
- Tables break across pages (row-level `break-inside: avoid`, not table-level)
- `orphans: 3; widows: 3` on paragraphs and list items
- Code blocks have blue left border (echoes blockquote visual language)
- Links inherit body font inline; only `http` URLs switch to monospace

## Available CSS Components

Built into `template.html` — use via `{.class}` attr_list or custom HTML:

| Component | Class/Element | Use for |
|-----------|--------------|---------|
| Cover (dark) | `.cover.cover--dark` | Dark gradient title page |
| Cover (light) | `.cover.cover--light` | White title page |
| Blockquote | `<blockquote>` | Notes, context (blue left border) |
| Callout | `.callout` | Editorial pull-quote (serif italic, ink border) |
| Status dots | `.b.bd` `.b.bp` `.b.bm` `.b.bx` `.b.br` | Green/amber/slate/violet/red dots |
| Caption | `.caption` or `<figcaption>` | Image/figure captions |
| Page break | `.new-page` | Force page break before element |
| Image sizes | `.img--half` `.img--sm` | 48% width / 200px max |
| Footnotes | `.footnotes` | Footnote section (top border, small text) |
| Definition list | `<dl>/<dt>/<dd>` | Term-definition pairs |

**Emoji → badge mapping** (auto-replaced by render.py):
`✅` → green dot, `🔶` → amber dot, `🚫` → violet dot, `⛔` → red dot, `❌` → slate dot

## When to Write Custom HTML vs Auto-Convert

| Situation | Approach |
|-----------|----------|
| Standard prose, specs, READMEs | Auto-convert via `render.py` |
| Needs colored section accents, charts, complex layout | Write custom HTML using template.html CSS |
| Complex tables with merged cells or custom columns | Write custom HTML |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Fonts look different on Linux vs macOS | System fonts vary — DejaVu on Linux, San Francisco on macOS. Consistent enough for print. |
| Cover page not filling page | Uses `padding-top: 200mm` to push content to bottom of A4. Adjust if needed. |
| WeasyPrint missing on system | Needs Pango/Cairo/HarfBuzz system libs. On Debian: `apt install libpango-1.0-0` |
| Large table leaves blank gap | Tables use `break-inside: auto` with row-level avoidance |
| Text garbled when copy-pasting | That was the old Playwright bug. WeasyPrint produces proper text layers. |
