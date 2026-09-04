"""Web-mode L2 checks (KUT-215) — RED-first against F2's real checks.json.

Each test builds a small synthetic target page that mirrors carrot.labs'
structure (same section ids / nesting as F2's dom_refs), then runs kit's
check executor with F2's actual check definitions.
"""
import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import kit  # noqa: E402

F2 = Path("/kirr.dev-112/apps/kitcut/test/results/2026-08-17T07-40-18Z-kitcut-v2-example-source")

HEXES = ["#2D5016", "#333333", "#4CAF50", "#666666", "#F1F8F4", "#FF6B35"]

PAGE = """<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="assets/css/style.css">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"></script>
</head>
<body>
<main>
<section id="hero" class="hero">
  <div class="overlay"></div>
  <div class="content"><div class="card">
    <div class="logo"><span>c</span><h1>Carrot Labs</h1></div>
    <h2>Fresh Carrots Delivered to Your Burrow!</h2>
    <button class="btn hero-cta" onclick="document.querySelector('#contact').scrollIntoView()">Get Your Carrots</button>
  </div></div>
</section>
<section id="weather">
  <div><div><div><i class="weather-icon fa-sun"></i><h1 id="temp">72</h1></div></div></div>
  <script>fetch('https://api.open-meteo.com/v1/forecast')</script>
</section>
<section id="freshest"><div><div><div><img src="images/carrots.png" alt="Fresh carrots"></div></div></div></section>
<section id="fast"><div><div><div><div><img src="images/rabbit1.png" alt="Delivery rabbit"></div></div></div></div></section>
<section id="happy"><div><div><div><img src="images/happyfamily.jpg" alt="Happy family"></div></div></div></section>
<section id="contact">
  <div><div><div>
    <form id="contactForm">
      <div><input type="text"></div>
      <div><input type="email"></div>
      <button type="submit">Contact Us</button>
    </form>
  </div></div></div>
  <script>document.querySelector('#contactForm').addEventListener('submit', e => e.preventDefault())</script>
</section>
</main>
<footer class="footer"><div></div><div><div><a>About</a></div></div></footer>
</body>
</html>
"""

CSS = ":root{" + "".join(
    f"--c{i}: {h};" for i, h in enumerate(HEXES)
) + "} body{font-family: Inter, Poppins, sans-serif;}"


@pytest.fixture()
def art():
    return kit.load_artifact(F2)


@pytest.fixture()
def target(tmp_path):
    t = tmp_path / "target"
    (t / "assets" / "css").mkdir(parents=True)
    (t / "index.html").write_text(PAGE)
    (t / "assets" / "css" / "style.css").write_text(CSS)
    return t


def get_check(art, kind):
    for c in art.checks.get("L2_structural", []) + art.checks.get("L2_structural_order", []):
        if c.get("check") == kind:
            return c
    raise AssertionError(f"F2 has no {kind} check")


class TestTokens:
    def test_color_tokens_present_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "color_tokens_present"))
        assert out["passed"], out

    def test_color_tokens_present_fail_on_missing_hex(self, art, target):
        css = (target / "assets/css/style.css").read_text().replace("#FF6B35", "#FF0000")
        (target / "assets/css/style.css").write_text(css)
        out = kit._check_L2(art, target, get_check(art, "color_tokens_present"))
        assert not out["passed"]

    def test_font_families_loaded_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "font_families_loaded"))
        assert out["passed"], out

    def test_font_families_loaded_fail(self, art, target):
        for f in ("index.html", "assets/css/style.css"):
            (target / f).write_text((target / f).read_text().replace("Poppins", "Arial"))
        out = kit._check_L2(art, target, get_check(art, "font_families_loaded"))
        assert not out["passed"]


class TestDomRefs:
    def test_dom_refs_resolve_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "dom_refs_resolve"))
        assert out["passed"], out.get("actual")

    def test_dom_refs_resolve_fail_on_removed_node(self, art, target):
        html = (target / "index.html").read_text().replace('<form id="contactForm">', "<div>")
        (target / "index.html").write_text(html)
        out = kit._check_L2(art, target, get_check(art, "dom_refs_resolve"))
        assert not out["passed"]


class TestOrder:
    def test_section_order_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "section_order"))
        assert out["passed"], out.get("actual")

    def test_section_order_fail_on_shuffle(self, art, target):
        """Negative control from KUT-215 AC: a shuffled page must fail."""
        html = (target / "index.html").read_text()
        hero = html[html.index('<section id="hero"'):html.index('<section id="weather"')]
        weather = html[html.index('<section id="weather"'):html.index('<section id="freshest"')]
        shuffled = html.replace(hero + weather, weather + hero)
        assert shuffled != html
        (target / "index.html").write_text(shuffled)
        out = kit._check_L2(art, target, get_check(art, "section_order"))
        assert not out["passed"]


class TestBehavior:
    def test_cta_scroll_target_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "cta_scroll_target"))
        assert out["passed"], out

    def test_cta_scroll_target_fail_without_target_wiring(self, art, target):
        html = (target / "index.html").read_text().replace(
            "document.querySelector('#contact').scrollIntoView()", "void(0)")
        (target / "index.html").write_text(html)
        out = kit._check_L2(art, target, get_check(art, "cta_scroll_target"))
        assert not out["passed"]

    def test_external_hosts_subset_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "external_hosts_subset"))
        assert out["passed"], out.get("actual")

    def test_external_hosts_subset_fail_on_rogue_host(self, art, target):
        html = (target / "index.html").read_text().replace(
            "</body>", '<script src="https://evil.example.com/x.js"></script></body>')
        (target / "index.html").write_text(html)
        out = kit._check_L2(art, target, get_check(art, "external_hosts_subset"))
        assert not out["passed"]

    def test_external_hosts_subset_ignores_anchor_hrefs(self, art, target):
        """KUT-218: <a href> is navigation, not a load-time request — the
        allowlist derives from network.har, so anchors must not fail it
        (F2's own footer carries daisyui.com/tailwindcss.com attribution)."""
        html = (target / "index.html").read_text().replace(
            "<a>About</a>",
            '<a>About</a><a href="https://daisyui.com" class="link">DaisyUI</a>'
            '<a href="https://tailwindcss.com" class="link">Tailwind CSS</a>')
        (target / "index.html").write_text(html)
        out = kit._check_L2(art, target, get_check(art, "external_hosts_subset"))
        assert out["passed"], out.get("actual")

    def test_form_no_real_submit_pass(self, art, target):
        out = kit._check_L2(art, target, get_check(art, "form_no_real_submit"))
        assert out["passed"], out

    def test_form_no_real_submit_fail_on_real_action(self, art, target):
        html = (target / "index.html").read_text()
        html = html.replace('<form id="contactForm">',
                            '<form id="contactForm" action="https://api.example.com/leads" method="POST">')
        html = html.replace("e.preventDefault()", "true")
        (target / "index.html").write_text(html)
        out = kit._check_L2(art, target, get_check(art, "form_no_real_submit"))
        assert not out["passed"]
