#!/usr/bin/env python3
"""
render.py — Convert markdown to styled PDF using WeasyPrint
Usage: python3 render.py input.md output.pdf [--title "Title"] [--subtitle "Sub"] [--date "Date"] [--dark] [--cover]

Dependencies: pip install markdown weasyprint
"""
import argparse
import re
import base64
from pathlib import Path
from urllib.parse import unquote

import markdown
from weasyprint import HTML

SKILL_DIR = Path(__file__).parent
TEMPLATE = SKILL_DIR / "template.html"

# ── Emoji → HTML badge mapping ───────────────────────────────────────────────
BADGE_MAP = {
    "✅": '<span class="b bd">●</span>',
    "🔶": '<span class="b bp">●</span>',
    "🚫": '<span class="b bx">●</span>',
    "⛔": '<span class="b br">●</span>',
    "❌": '<span class="b bm">●</span>',
}


def parse_args():
    p = argparse.ArgumentParser(description="Convert markdown to styled PDF")
    p.add_argument("input", help="Path to input .md file")
    p.add_argument("output", help="Path to output .pdf file")
    p.add_argument("--title", default="", help="Document title (overrides first H1)")
    p.add_argument("--subtitle", default="", help="Subtitle on cover")
    p.add_argument("--date", default="", help="Date on cover")
    p.add_argument("--org", default="", help="Organization name on cover")
    p.add_argument("--dark", action="store_true", help="Dark gradient cover")
    p.add_argument("--cover", action="store_true", help="Show cover page (off by default)")
    return p.parse_args()


def extract_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def preprocess_strikethrough(md_text: str) -> str:
    return re.sub(r'~~(.+?)~~', r'<del>\1</del>', md_text, flags=re.DOTALL)


def md_to_html(md_text: str) -> str:
    md_text = preprocess_strikethrough(md_text)
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "attr_list", "footnotes"],
    )


def replace_emoji_badges(html: str) -> str:
    for emoji, span in BADGE_MAP.items():
        html = html.replace(emoji, span)
    return html


# ── Section color mapping (H2 headings → colored left-border accent) ─────────
SECTION_COLORS = {
    "introduction":    "#059669",  # green
    "methodology":     "#2563eb",  # blue
    "analysis":        "#7c3aed",  # violet
    "results":         "#d97706",  # amber
    "discussion":      "#dc2626",  # red
    "conclusion":      "#0891b2",  # cyan
    "summary":         "#475569",  # slate
    "appendix":        "#64748b",  # gray
}


def colorize_sections(html: str) -> str:
    """Add colored accent dots before H2 headings matching known section names."""
    for keyword, color in SECTION_COLORS.items():
        pattern = re.compile(
            rf'(<h2[^>]*>)([^<]*{re.escape(keyword)}[^<]*)(</h2>)',
            re.IGNORECASE,
        )
        html = pattern.sub(
            rf'\1<span style="display:inline-block;width:4px;height:14px;'
            rf'background:{color};border-radius:2px;margin-right:8px;vertical-align:middle"></span>'
            rf'\2\3',
            html,
        )
    return html


def embed_local_images(html: str, base_dir: Path) -> str:
    for match in re.finditer(r'<img[^>]*src="([^"]*)"[^>]*/?>',  html):
        src = unquote(match.group(1))
        if src.startswith(("data:", "http")):
            continue
        path = base_dir / src
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode()
            ext = path.suffix.lstrip(".").lower()
            if ext == "jpg":
                ext = "jpeg"
            html = html.replace(
                match.group(0),
                match.group(0).replace(match.group(1), f"data:image/{ext};base64,{data}"),
            )
    return html


def _meta_item(label: str, value: str) -> str:
    return (
        '<div class="cover-meta-item">'
        f'<div class="cover-meta-label">{label}</div>'
        f'<div class="cover-meta-value">{value}</div>'
        "</div>"
    )


def build_cover(title: str, subtitle: str, date: str, org: str, dark: bool) -> str:
    variant = "cover--dark" if dark else "cover--light"
    meta_items = ""
    if date:
        meta_items += _meta_item("Date", date)
    if org:
        meta_items += _meta_item("Organization", org)
    meta_html = f'<div class="cover-meta">{meta_items}</div>' if meta_items else ""
    return (
        f'<div class="cover {variant}">'
        f'<div class="cover-subtitle">{subtitle}</div>'
        f'<div class="cover-title">{title}</div>'
        f'{meta_html}'
        "</div>"
    )


def main():
    args = parse_args()
    input_path = Path(args.input)
    md_text = input_path.read_text()

    title = args.title or extract_title(md_text, input_path.stem)

    # Markdown → HTML → post-process
    content = md_to_html(md_text)
    content = replace_emoji_badges(content)
    content = colorize_sections(content)
    content = embed_local_images(content, input_path.parent)

    # Cover
    cover = build_cover(title, args.subtitle, args.date, args.org, args.dark) if args.cover else ""

    # Assemble: template + content
    template = TEMPLATE.read_text()
    html = template.replace("{{title}}", title)
    html = html.replace("{{cover}}", cover)
    html = html.replace("{{content}}", content)

    # Inject @page :first margin override only when cover is present
    if args.cover:
        html = html.replace(
            "@page cover { margin: 0; }",
            "@page :first { margin: 0; }\n@page cover { margin: 0; }",
        )

    # Render with WeasyPrint
    HTML(string=html).write_pdf(args.output)
    print(f"✓ {args.output}")


if __name__ == "__main__":
    main()
