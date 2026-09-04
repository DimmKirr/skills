#!/usr/bin/env python3
"""kit — deterministic reader/verifier for kitcut-artifact/2.0 bundles.

Subcommands (all print JSON to stdout):
  plan   <artifact> --target <dir>    diff facts vs lockfile -> create/regenerate/keep/delete
  next   <artifact> --target <dir>    context package for the next unbuilt unit
  record <artifact> --target <dir> --unit <id> --files f1 f2 ...
  verify <artifact> --target <dir>    execute checks.json L1/L2; emit L3/L4 items

stdlib only. Never calls a model. See references/artifact-spec.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SPEC = "kitcut-artifact/2.0.0-draft"
LOCK_SPEC = "kitcut-lock/1.0.0-draft"
LOCK_NAME = ".kit-lock.json"

RESOURCE_TYPES = {
    "tofukit_project", "tofukit_feature", "tofukit_file",
    "tofukit_library", "tofukit_language", "tofukit_integration",
}
PROVENANCE = {"detected", "inferred", "prose-extracted"}
ROLES = {
    "contains", "implemented_by", "verified_by", "tests",
    "uses_library", "uses_integration", "uses_image",
    "styled_by", "styled_by_file", "uses_font", "uses_design_system",
    "animated_by", "triggers", "navigates_to", "written_in", "reads_config",
}
# roles where generating src requires dst to exist first (unit dependency)
DEP_ROLES = ROLES - {"contains"}


class ArtifactError(Exception):
    pass


class Unit:
    def __init__(self, uid: str, resources: list[str]):
        self.id = uid
        self.resources = resources  # resource ids

    def __repr__(self):
        return f"Unit({self.id}, {len(self.resources)} resources)"


class Artifact:
    def __init__(self, path: Path, facts: dict, meta: dict, checks: dict,
                 requirements: dict[str, str], digests: dict, warnings: list[str]):
        self.path = path
        self.facts = facts
        self.meta = meta
        self.checks = checks
        self.requirements = requirements  # resource name -> prose text
        self.digests = digests            # digest name -> parsed json
        self.warnings = warnings
        self.resources = facts["resources"]
        self.edges = facts["edges"]
        self.root = facts["root"]
        self.by_id = {r["id"]: r for r in self.resources}


# ---------------------------------------------------------------- load

def load_artifact(path: str | Path) -> Artifact:
    b = Path(path)
    if not (b / "facts.json").exists():
        raise ArtifactError(f"not an artifact bundle (no facts.json): {b}")
    facts = json.loads((b / "facts.json").read_text())
    meta = json.loads((b / "meta.json").read_text()) if (b / "meta.json").exists() else {}
    checks = json.loads((b / "checks.json").read_text()) if (b / "checks.json").exists() else {}

    errs: list[str] = []
    warns: list[str] = []

    if facts.get("spec") != SPEC:
        errs.append(f"facts.spec must be {SPEC}")
    resources = facts.get("resources", [])
    edges = facts.get("edges", [])
    ids = [r["id"] for r in resources]
    if len(ids) != len(set(ids)):
        errs.append("duplicate resource ids")
    idset = set(ids)
    root = facts.get("root")
    if root not in idset:
        errs.append(f"root does not resolve: {root}")

    for r in resources:
        if r.get("type") not in RESOURCE_TYPES:
            errs.append(f"{r.get('id')}: unknown type {r.get('type')}")
        if r.get("provenance") not in PROVENANCE:
            errs.append(f"{r.get('id')}: bad provenance")
        if not re.fullmatch(r"[a-z0-9_]+", r.get("name", "")):
            errs.append(f"{r.get('id')}: bad name")

    # V1 dangling + role vocabulary
    for e in edges:
        if e.get("src") not in idset or e.get("dst") not in idset:
            errs.append(f"V1 dangling edge: {e.get('src')} -> {e.get('dst')}")
        if e.get("role") not in ROLES:
            errs.append(f"unknown edge role: {e.get('role')}")
        if e.get("provenance") not in PROVENANCE:
            errs.append("edge missing/bad provenance")

    # V2 orphans (BFS from root)
    if root in idset:
        adj: dict[str, list[str]] = {}
        for e in edges:
            adj.setdefault(e["src"], []).append(e["dst"])
        seen, stack = {root}, [root]
        while stack:
            for d in adj.get(stack.pop(), []):
                if d not in seen:
                    seen.add(d)
                    stack.append(d)
        orphans = sorted(idset - seen)
        if orphans:
            errs.append(f"V2 orphans (unreachable from root): {orphans[:5]}"
                        + (f" +{len(orphans) - 5} more" if len(orphans) > 5 else ""))

    # Profile: distribution bundles ship no evidence/. In every profile,
    # resource `path` attributes are generation targets — evidence never
    # mirrors them; check-reference availability is handled at verify time
    # (L3 skip rule).
    profile = "full" if (b / "evidence").exists() else "distribution"

    # V4 prose coverage both directions
    claimed = {r["requirements"]: r["id"] for r in resources if r.get("requirements")}
    for c in claimed:
        if not (b / c).exists():
            errs.append(f"V4 missing prose file: {c}")
    req_dir = b / "requirements"
    if req_dir.exists():
        on_disk = {f"requirements/{p.name}" for p in req_dir.glob("*.md")}
        for u in sorted(on_disk - set(claimed)):
            errs.append(f"V4 orphan prose (no resource claims it): {u}")

    # V5 no ${ in prose
    requirements: dict[str, str] = {}
    for c, rid in claimed.items():
        f = b / c
        if f.exists():
            text = f.read_text()
            if "${" in text:
                errs.append(f"V5 interpolation in prose: {c}")
            requirements[Path(c).stem] = text

    # V6 animated_by/triggers -> dom_ref (warn)
    by_id = {r["id"]: r for r in resources}
    for e in edges:
        if e.get("role") in ("animated_by", "triggers") and e.get("src") in by_id:
            if not by_id[e["src"]].get("attributes", {}).get("dom_ref"):
                warns.append(f"V6 {e['role']} src lacks dom_ref: {e['src']}")

    # V10 distribution hygiene (warn): views/ holds producer-internal
    # projections and must not ship in distribution bundles.
    if profile == "distribution" and (b / "views").exists():
        warns.append("V10 distribution bundle ships views/ (producer-internal; remove)")

    # V9 linking-imperative lint (warn)
    lint = re.compile(r"tofulink|must link|tofukit_(feature|file|library|integration)\b", re.I)
    for name, text in requirements.items():
        if lint.search(text):
            warns.append(f"V9 linking imperative in requirements/{name}.md")

    if errs:
        raise ArtifactError("; ".join(errs))

    digests = {}
    dig_dir = b / "digests"
    if dig_dir.exists():
        for p in dig_dir.glob("*.json"):
            digests[p.stem] = json.loads(p.read_text())

    art = Artifact(b, facts, meta, checks, requirements, digests, warns)
    art.profile = profile
    return art


# ---------------------------------------------------------------- units

def build_units(art: Artifact) -> list[Unit]:
    """Deterministic unit clustering + topological ordering."""
    assigned: dict[str, str] = {}  # resource id -> unit id

    # scaffold: root + stack
    for r in art.resources:
        if r["id"] == art.root or r["category"] in ("root", "stack"):
            assigned[r["id"]] = "scaffold"

    # one unit per feature that owns files (implemented_by / verified_by / contains file)
    for r in art.resources:
        if r["type"] != "tofukit_feature" or r["id"] in assigned:
            continue
        owned = [e["dst"] for e in art.edges
                 if e["src"] == r["id"]
                 and e["role"] in ("implemented_by", "verified_by", "contains")
                 and art.by_id[e["dst"]]["type"] == "tofukit_file"]
        if owned:
            assigned[r["id"]] = r["name"]
            for f in owned:
                assigned.setdefault(f, r["name"])

    # everything else: unit per top-level category segment
    for r in art.resources:
        if r["id"] not in assigned:
            assigned[r["id"]] = r["category"].replace("/", "_")

    units: dict[str, list[str]] = {}
    for rid, uid in assigned.items():
        units.setdefault(uid, []).append(rid)
    for members in units.values():
        members.sort()

    # unit dependency edges (src unit depends on dst unit)
    deps: dict[str, set[str]] = {u: set() for u in units}
    for e in art.edges:
        su, du = assigned[e["src"]], assigned[e["dst"]]
        if su == du:
            continue
        if e["role"] in DEP_ROLES:
            deps[su].add(du)
        elif e["role"] == "contains" and e["src"] != art.root:
            # a page/section assembling children needs them first
            deps[su].add(du)

    # Kahn topo, deterministic tie-break (scaffold first, then alphabetical)
    order: list[str] = []
    remaining = dict(deps)
    while remaining:
        ready = sorted([u for u, d in remaining.items() if not (d & set(remaining))],
                       key=lambda u: (u != "scaffold", u))
        if not ready:  # cycle: break deterministically
            ready = [sorted(remaining)[0]]
        for u in ready:
            order.append(u)
            del remaining[u]
    return [Unit(u, units[u]) for u in order]


def _unit_facts_hash(art: Artifact, unit: Unit) -> str:
    rset = set(unit.resources)
    slice_ = {
        "resources": sorted((art.by_id[r] for r in unit.resources), key=lambda r: r["id"]),
        "edges": sorted((e for e in art.edges if e["src"] in rset or e["dst"] in rset),
                        key=lambda e: (e["src"], e["role"], e["dst"])),
    }
    blob = json.dumps(slice_, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode()).hexdigest()


# ---------------------------------------------------------------- lockfile

def _load_lock(target: Path) -> dict:
    p = target / LOCK_NAME
    if p.exists():
        return json.loads(p.read_text())
    return {"spec": LOCK_SPEC, "artifact": {}, "units": {}}


def _save_lock(target: Path, lock: dict) -> None:
    (target / LOCK_NAME).write_text(json.dumps(lock, indent=2))


def _sha256_file(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- plan

def plan(art: Artifact, target: str | Path) -> dict:
    target = Path(target)
    lock = _load_lock(target)
    units = build_units(art)
    current = {u.id: u for u in units}

    result = {"create": [], "regenerate": [], "keep": [], "delete": [], "drift": []}
    for u in units:  # topo order
        rec = lock["units"].get(u.id)
        if rec is None:
            result["create"].append(u.id)
        elif rec.get("facts_hash") != _unit_facts_hash(art, u):
            result["regenerate"].append(u.id)
        else:
            result["keep"].append(u.id)
            for rel, h in rec.get("files", {}).items():
                f = target / rel
                if not f.exists() or _sha256_file(f) != h:
                    result["drift"].append({"unit": u.id, "file": rel})
    for uid in sorted(lock["units"]):
        if uid not in current:
            result["delete"].append(uid)
    return result


# ---------------------------------------------------------------- next

_INTERFACE_ATTRS = ("path", "version", "hex", "css_variable", "dom_ref")


def next_unit(art: Artifact, target: str | Path) -> dict:
    target = Path(target)
    p = plan(art, target)
    todo = [u for u in (u.id for u in build_units(art))
            if u in p["create"] or u in p["regenerate"]]
    if not todo:
        return {"done": True}
    uid = todo[0]
    unit = next(u for u in build_units(art) if u.id == uid)
    rset = set(unit.resources)

    lock = _load_lock(target)
    dep_interfaces = []
    for dep_id, rec in sorted(lock["units"].items()):
        if dep_id == uid:
            continue
        dep_interfaces.append({
            "unit": dep_id,
            "resources": [
                {k: r[k] for k in ("id", "type", "name", "category") if k in r}
                | {"attributes": {a: v for a, v in r.get("attributes", {}).items()
                                  if a in _INTERFACE_ATTRS}}
                for r in (art.by_id[rid] for rid in rec.get("resources", [])
                          if rid in art.by_id)
            ],
            "files": rec.get("files", {}),
        })

    return {
        "done": False,
        "unit": uid,
        "resources": [art.by_id[r] for r in unit.resources],
        "edges": [e for e in art.edges if e["src"] in rset or e["dst"] in rset],
        "requirements": {
            name: text for name, text in art.requirements.items()
            if any(art.by_id[r]["name"] == name for r in unit.resources)
        },
        "digests": art.digests,
        "dep_interfaces": dep_interfaces,
    }


# ---------------------------------------------------------------- record

def record(art: Artifact, target: str | Path, unit_id: str, files: list[str]) -> dict:
    target = Path(target)
    units = {u.id: u for u in build_units(art)}
    if unit_id not in units:
        raise ArtifactError(f"unknown unit: {unit_id} (have: {sorted(units)})")
    hashes = {}
    for rel in files:
        f = target / rel
        if not f.exists():
            raise ArtifactError(f"recorded file missing in target: {rel}")
        hashes[rel] = _sha256_file(f)
    lock = _load_lock(target)
    lock["artifact"] = {"path": str(art.path)}
    lock["units"][unit_id] = {
        "resources": units[unit_id].resources,
        "files": hashes,
        "facts_hash": _unit_facts_hash(art, units[unit_id]),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_lock(target, lock)
    return lock["units"][unit_id]


# ---------------------------------------------------------------- verify

def _run(cmd: str, cwd: Path, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)


def _go_files(target: Path):
    return [p for p in target.rglob("*.go")]


def _go_imports(target: Path) -> set[str]:
    imps: set[str] = set()
    single = re.compile(r'^import\s+"([^"]+)"', re.M)
    block = re.compile(r"import\s*\(([^)]*)\)", re.S)
    for f in _go_files(target):
        src = f.read_text()
        imps.update(single.findall(src))
        for b in block.findall(src):
            imps.update(re.findall(r'"([^"]+)"', b))
    return imps


# ---- minimal DOM + CSS-selector subset (tag, #id, .class, :nth-of-type, '>', ' ') ----

class _Node:
    __slots__ = ("tag", "attrs", "children", "parent", "pos")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children: list[_Node] = []
        self.pos = 0  # pre-order document position


_VOID = {"meta", "link", "img", "input", "br", "hr", "source", "area", "base",
         "col", "embed", "track", "wbr"}


def _parse_dom(html_text: str) -> _Node:
    import html.parser

    root = _Node("#root", {}, None)

    class P(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.cur = root
            self.n = 0

        def handle_starttag(self, tag, attrs):
            self.n += 1
            node = _Node(tag, attrs, self.cur)
            node.pos = self.n
            self.cur.children.append(node)
            if tag not in _VOID:
                self.cur = node

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if tag not in _VOID and self.cur.tag == tag:
                self.cur = self.cur.parent

        def handle_endtag(self, tag):
            if tag in _VOID:
                return
            c = self.cur
            while c is not root and c.tag != tag:
                c = c.parent
            if c is not root:
                self.cur = c.parent

    p = P()
    p.feed(html_text)
    return root


_PART = re.compile(r"^([a-zA-Z0-9]+)?(#[\w-]+)?((?:\.[\w-]+)*)(?::nth-of-type\((\d+)\))?$")


def _match_part(node: _Node, part: str) -> bool:
    m = _PART.match(part)
    if not m:
        return False
    tag, id_, classes, nth = m.groups()
    if tag and node.tag != tag.lower():
        return False
    if id_ and node.attrs.get("id") != id_[1:]:
        return False
    if classes:
        have = set((node.attrs.get("class") or "").split())
        if not set(classes.strip(".").split(".")) <= have:
            return False
    if nth:
        siblings = [c for c in node.parent.children if c.tag == node.tag] if node.parent else [node]
        if siblings.index(node) + 1 != int(nth):
            return False
    return True


def _tokenize_selector(sel: str) -> list[tuple[str, str]]:
    """-> [(part, combinator_before)] where combinator is '>' or ' ' ('' for first)."""
    toks, comb = [], ""
    for raw in re.split(r"(\s*>\s*|\s+)", sel.strip()):
        raw = raw.strip() if raw else ""
        if raw == ">":
            comb = ">"
        elif raw == "":
            if comb != ">":
                comb = " "
        else:
            toks.append((raw, comb if toks else ""))
            comb = " "
    return toks


def _select(root: _Node, sel: str) -> list[_Node]:
    parts = _tokenize_selector(sel)
    if not parts:
        return []

    def all_nodes(n):
        for c in n.children:
            yield c
            yield from all_nodes(c)

    def chain_matches(node: _Node, idx: int) -> bool:
        part, comb = parts[idx]
        if not _match_part(node, part):
            return False
        if idx == 0:
            return True
        prev_comb = parts[idx][1]
        if prev_comb == ">":
            return node.parent is not None and chain_matches(node.parent, idx - 1)
        anc = node.parent
        while anc is not None and anc.tag != "#root":
            if chain_matches(anc, idx - 1):
                return True
            anc = anc.parent
        return False

    return [n for n in all_nodes(root) if chain_matches(n, len(parts) - 1)]


def _web_files(target: Path, exts=(".html", ".css", ".js")):
    return [p for p in target.rglob("*") if p.suffix in exts and p.is_file()]


def _read_all_web(target: Path) -> str:
    return "\n".join(p.read_text(errors="ignore") for p in _web_files(target))


def _index_dom(target: Path) -> _Node:
    return _parse_dom((target / "index.html").read_text(errors="ignore"))


def _resource_urls(target: Path) -> set[str]:
    """URLs that cause network requests at load/runtime.

    The external-hosts allowlist derives from evidence/network.har, so only
    request-producing URLs are subject to it: src attributes, <link href>,
    CSS url(...), and URL literals inside script code. Anchor href is
    navigation — no request until clicked — and is excluded (KUT-218).
    """
    urls: set[str] = set()
    for p in _web_files(target):
        text = p.read_text(errors="ignore")
        if p.suffix == ".html":
            urls.update(re.findall(r'\bsrc=["\'](https?://[^"\']+)', text))
            urls.update(re.findall(r'<link\b[^>]*\bhref=["\'](https?://[^"\']+)', text, re.I))
            urls.update(re.findall(r'url\(\s*["\']?(https?://[^"\')\s]+)', text))
            for script in re.findall(r"<script\b[^>]*>(.*?)</script>", text, re.S | re.I):
                urls.update(re.findall(r'https?://[^"\'\s)]+', script))
        else:
            urls.update(re.findall(r'https?://[^"\'\s)]+', text))
    return urls


def _check_web_L2(art: Artifact, target: Path, c: dict) -> dict | None:
    """Web-mode checks; returns None if kind not handled here."""
    kind = c.get("check")
    out = dict(c)
    if kind == "color_tokens_present":
        text = (target / c["file"]).read_text(errors="ignore").lower() if (target / c["file"]).exists() else ""
        missing = [h for h in c["hex"] if h.lower() not in text]
        out["passed"] = not missing
        if missing:
            out["actual"] = {"missing_hex": missing}
    elif kind == "font_families_loaded":
        blob = _read_all_web(target).lower()
        missing = [f for f in c["families"] if f.lower() not in blob]
        out["passed"] = not missing
        if missing:
            out["actual"] = {"missing_families": missing}
    elif kind == "dom_refs_resolve":
        root = _index_dom(target)
        bad = [s for s in c["selectors"] if len(_select(root, s)) == 0]
        out["passed"] = not bad
        if bad:
            out["actual"] = {"unresolved": bad}
    elif kind == "section_order":
        root = _index_dom(target)
        by_name = {r["name"]: r for r in art.resources}
        positions, problems = [], []
        for name in c["expect"]:
            ref = by_name.get(name, {}).get("attributes", {}).get("dom_ref")
            nodes = _select(root, ref) if ref else []
            if not nodes:
                problems.append(f"{name}: dom_ref unresolved ({ref})")
            else:
                positions.append((nodes[0].pos, name))
        in_order = all(positions[i][0] < positions[i + 1][0] for i in range(len(positions) - 1))
        out["passed"] = not problems and in_order
        if not out["passed"]:
            out["actual"] = {"problems": problems,
                            "observed_order": [n for _, n in sorted(positions)]}
    elif kind == "cta_scroll_target":
        root = _index_dom(target)
        html_blob = _read_all_web(target)
        to_sel = c["to"]
        to_id = to_sel.split("#")[-1] if "#" in to_sel else None
        wired = bool(to_id) and re.search(rf"#{re.escape(to_id)}\b", html_blob) is not None
        out["passed"] = bool(_select(root, c["from"])) and bool(_select(root, to_sel)) and wired
    elif kind == "external_hosts_subset":
        hosts = set()
        for u in _resource_urls(target):
            m = re.match(r"https?://([^/\"'\s)]+)", u)
            if m:
                hosts.add(m.group(1))
        extra = sorted(h for h in hosts if h not in set(c["allow"]))
        out["passed"] = not extra
        if extra:
            out["actual"] = {"disallowed_hosts": extra}
    elif kind == "form_no_real_submit":
        root = _index_dom(target)
        forms = _select(root, c["selector"])
        if not forms:
            out["passed"] = False
            out["actual"] = "form selector unresolved"
        else:
            action = forms[0].attrs.get("action", "")
            real_action = action.startswith("http") or (action and action not in ("#",))
            prevented = "preventDefault" in _read_all_web(target)
            out["passed"] = prevented and not real_action
    else:
        return None
    return out


def _check_L2(art: Artifact, target: Path, c: dict) -> dict:
    kind = c.get("check")
    out = dict(c)
    try:
        web = _check_web_L2(art, target, c)
        if web is not None:
            return web
        if kind == "binary_stdout":
            r = _run(c["run"], target)
            out["passed"] = (r.returncode == 0 and r.stdout == c["expect_stdout"])
            if not out["passed"]:
                out["actual"] = r.stdout[-500:] or r.stderr[-500:]
        elif kind == "symbol_exists":
            pat = re.compile(
                rf"func\s+{re.escape(c['symbol'])}\s*\([^)]*\)\s*{re.escape(c.get('returns') or '')}")
            out["passed"] = any(pat.search(f.read_text()) for f in _go_files(target))
        elif kind == "test_asserts_literal":
            tests = [f for f in _go_files(target) if f.name.endswith("_test.go")]
            out["passed"] = any(c["literal"] in f.read_text() for f in tests)
        elif kind == "no_external_deps":
            extra = _go_imports(target) - set(c["allow_imports"])
            out["passed"] = not extra
            if extra:
                out["actual"] = sorted(extra)
        elif kind == "files_exist":
            missing = [f for f in c["files"] if not (target / f).exists()]
            out["passed"] = not missing
            if missing:
                out["actual"] = missing
        else:
            out["passed"] = False
            out["error"] = f"check kind not implemented: {kind}"
    except Exception as exc:  # noqa: BLE001 — verify must report, not crash
        out["passed"] = False
        out["error"] = str(exc)
    return out


def verify(art: Artifact, target: str | Path) -> dict:
    target = Path(target)
    result = {"L1": [], "L2": [], "L3_items": [], "L4_items": [], "warnings": art.warnings}

    for c in art.checks.get("L1_build", []):
        out = dict(c)
        try:
            if "run" in c:
                r = _run(c["run"], target)
                out["passed"] = r.returncode == 0
                if not out["passed"]:
                    out["actual"] = (r.stdout + r.stderr)[-800:]
            elif c.get("check") == "files_exist":
                missing = [f for f in c["files"] if not (target / f).exists()]
                out["passed"] = not missing
            elif c.get("check") == "html_parses":
                import html.parser
                p = html.parser.HTMLParser()
                p.feed((target / c["file"]).read_text(errors="ignore"))
                out["passed"] = True
            else:
                out["passed"] = False
                out["error"] = "unknown L1 check"
        except Exception as exc:  # noqa: BLE001
            out["passed"] = False
            out["error"] = str(exc)
        result["L1"].append(out)

    for c in art.checks.get("L2_structural", []) + art.checks.get("L2_structural_order", []):
        result["L2"].append(_check_L2(art, target, c))

    # L3 items reference bundle files (screenshots); in distribution bundles
    # (or incomplete evidence) the reference is absent — emit as skipped,
    # never gate on it (spec §7).
    l3 = []
    for item in art.checks.get("L3_visual", []):
        item = dict(item)
        ref = item.get("reference")
        if ref and not (art.path / ref).exists():
            item["skipped"] = "reference unavailable"
        l3.append(item)
    result["L3_items"] = l3
    result["L4_items"] = list(art.checks.get("L4_acceptance", []))
    result["ok"] = (all(c["passed"] for c in result["L1"])
                    and all(c["passed"] for c in result["L2"]))
    return result


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kit", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "next", "record", "verify"):
        p = sub.add_parser(name)
        p.add_argument("artifact")
        p.add_argument("--target", required=True)
        if name == "record":
            p.add_argument("--unit", required=True)
            # empty list is legal: token/concept units are realized inside
            # other units' files (see SKILL.md)
            p.add_argument("--files", nargs="*", default=[])
    args = ap.parse_args(argv)

    try:
        art = load_artifact(args.artifact)
    except ArtifactError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    if args.cmd == "plan":
        print(json.dumps(plan(art, args.target), indent=2))
        return 0
    if args.cmd == "next":
        print(json.dumps(next_unit(art, args.target), indent=2))
        return 0
    if args.cmd == "record":
        try:
            print(json.dumps(record(art, args.target, args.unit, args.files), indent=2))
        except ArtifactError as exc:
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
            return 2
        return 0
    if args.cmd == "verify":
        res = verify(art, args.target)
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
