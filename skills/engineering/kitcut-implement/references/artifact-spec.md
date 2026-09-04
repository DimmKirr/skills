# kitcut artifact specification

**Version:** `kitcut-artifact/2.0.0-draft`
**Checks version:** `kitcut-checks/1.0.0-draft`
**Lockfile version:** `kitcut-lock/1.0.0-draft`

The artifact is the contract between a producer (`ingest` — closed, may be
cloud-hosted) and consumers (`edit`, `reproduce`/`kitcut-implement` — open).
A conforming consumer must be able to reproduce the described software from
the artifact alone, without the producer, the original site/repo, or any
prompt text baked at ingest time.

## 0. Bundle profiles (normative)

| Profile | `evidence/` | Purpose |
|---|---|---|
| **distribution** | absent | THE product: what ships to consumers. Reconstruction uses facts + requirements + digests + checks — nothing else exists. |
| **full** | present | producer-side/dev bundles: evidence enables L3 visual verification and producer validation. |

Profile is determined by the presence of `evidence/`. The cardinal rule in
both profiles: **evidence is never an input to reconstruction.** In a full
bundle, evidence exists solely for *verification* (L3 references) and
producer-side validation; a consumer that reads evidence during generation
— including copying image binaries — is non-conforming. Everything the
consumer needs to generate, including every image, must be expressible from
facts (descriptions, `model` hints, dom context) and requirements.

Machine-readable schemas: [facts.schema.json](facts.schema.json),
[checks.schema.json](checks.schema.json). `scripts/kit.py` enforces the
subset marked **enforced** below with a built-in validator (stdlib only —
full JSON Schema draft support is not required of consumers).

---

## 1. Bundle layout

```
artifact/
├── meta.json          # identity, provenance, algorithm pins
├── facts.json         # THE contract: resources[] + edges[] + root
├── checks.json        # executable definition of done (L1–L4)
├── requirements/      # per-resource declarative prose (*.md)
├── digests/           # deterministic projections of evidence (*.json)
└── evidence/          # immutable ground truth (crawl/source, screenshots, HAR)
```

| Layer | Authored by | Mutable by | Regenerable |
|---|---|---|---|
| meta | ingest | — | no |
| facts | ingest (detect + analyze) | edit | no |
| checks | ingest (L1–L3 compiled; L4 authored) | edit (L4 only) | L1–L3 yes |
| requirements | ingest (LLM, from evidence) | edit | no (carries judgment) |
| digests | ingest (deterministic) | — | yes, from evidence |
| evidence | ingest (crawl/copy) | **never** | no |

A bundle is a directory; it may travel as a zip or git repo. All paths inside
the bundle are relative, forward-slash.

## 2. meta.json

```json
{
  "spec": "kitcut-artifact/2.0.0-draft",
  "source": {"kind": "website|git_repo|local_path", "url|path": "...", "upstream": "..."},
  "produced_by": {"tool": "...", "version": "..."},
  "created": "ISO-8601",
  "digest_algorithms": {"dom-outline": "<version-or-hash>", "symbol-map": "..."},
  "counts": {"resources": 0, "edges": 0, "checks": 0}
}
```

- **enforced:** `spec` present and equal to a supported version.
- `digest_algorithms` pins the algorithm that produced each digest so any
  conforming tool can re-derive and compare. Absent pin ⇒ digests are
  advisory, `dom_position` comparisons across regenerations are invalid.

## 3. facts.json

```json
{
  "spec": "kitcut-artifact/2.0.0-draft",
  "root": "<resource id>",
  "resources": [ Resource... ],
  "edges": [ Edge... ]
}
```

### 3.1 Resource

```json
{
  "id": "tofukit_feature.ui_section_hero",     // "<type>.<name>", unique
  "type": "tofukit_project|tofukit_feature|tofukit_file|tofukit_library|tofukit_language|tofukit_integration",
  "name": "ui_section_hero",                    // [a-z0-9_]+
  "category": "root|stack|project|files|ui/...|cli/...|backend/...",
  "provenance": "detected|inferred|prose-extracted",
  "confidence": 0.0-1.0,                        // optional; required when inferred
  "requirements": "requirements/<name>.md",     // optional pointer, see §5
  "attributes": { ... }                         // optional, see below
}
```

Well-known attributes:

| Attribute | Meaning |
|---|---|
| `path` | file path relative to reproduction root (for `tofukit_file`) |
| `dom_ref` | CSS selector resolving to exactly one element in evidence |
| `dom_ref_source` | `static` (resolves in crawled HTML) or `rendered` (needs post-JS snapshot) |
| `dom_position` | 1-based document-order index among outline-captured elements; **sort key only**, meaningless absolutely; valid only against the pinned dom-outline digest |
| `hex`, `css_variable` | design-token values (colors) |
| `version` | library/language version |

- **enforced:** ids unique; `root` present and refers to an existing resource
  of type `tofukit_project`.

### 3.2 Edge

```json
{
  "src": "<resource id>", "role": "<role>", "dst": "<resource id>",
  "provenance": "detected|inferred|prose-extracted",
  "confidence": 0.0-1.0,
  "attributes": {"order": 1}     // optional; see ordering rules
}
```

Role vocabulary (closed set; extending it is a spec change):

| Role | src → dst |
|---|---|
| `contains` | structural parent → child (project→feature, page→section, section→component) |
| `implemented_by` | feature → file realizing it |
| `verified_by` | feature → test file/resource |
| `tests` | test file → file under test |
| `uses_library` | consumer → library |
| `uses_integration` | consumer → external service |
| `uses_image` | consumer → image file |
| `styled_by` | UI element → color/style token |
| `styled_by_file` | UI element → stylesheet file |
| `uses_font` | UI element → font token |
| `uses_design_system` | element/root → design-system resource |
| `animated_by` | UI element → animation |
| `triggers` | UI element → behavioral feature it initiates |
| `navigates_to` | behavioral feature → destination UI resource |
| `written_in` | project → language |
| `reads_config` | code resource → config key resource |

- **enforced:** every `src`/`dst` resolves to an existing resource (no
  dangling); `role` in vocabulary.

### 3.3 Ordering (normative)

- **Structural order** (which section is 1st/2nd on a page, subcommand order)
  = `attributes.order` on the `contains` edge. Dense integers from 1 within
  one parent.
- **Document order** of DOM-anchored elements = `dom_position` on the
  resource. Only comparisons are meaningful.
- Prose never carries order. A numbered list in requirements is narrative,
  not contract; verify checks generated output against edges, not prose.

### 3.4 Provenance (normative)

| Value | Meaning | Epistemic status |
|---|---|---|
| `detected` | deterministically measured from evidence (import AST, HAR host, DOM containment, CSS binding) | fact |
| `inferred` | LLM assertion during analysis, confidence attached | claim until verify corroborates |
| `prose-extracted` | recovered mechanically from textual sources rather than measured or reasoned | weakest fact class; verify should corroborate |

## 4. Prose rules (normative)

1. **Edges live only in facts.json.** Requirements prose is ref-free: no
   `${...}` interpolation of any form (**enforced:** reject prose containing
   `${`), and no linking imperatives ("must link", "tofulink",
   `tofukit_<type>` type names). Plain backticked resource-name *mentions*
   are allowed and carry zero semantic weight.
2. **Prompts are never stored.** Requirements are declarative observations +
   inferred intent; generation prompts are composed by the consumer at
   reproduce time.
3. **One resource = one prose file.** If a paragraph in a parent's file
   describes a child, it is misfiled — move it to the child.
4. **Coverage both directions** (**enforced**): every `requirements` pointer
   resolves to a file; every `requirements/*.md` is claimed by exactly one
   resource.

## 5. Evidence rules (normative)

0. **Verification-only**: evidence is never read during generation,
   in any profile. `path` attributes on resources are **generation targets**
   (where the consumer must write the file), not evidence pointers.
1. **Immutable.** Written once by ingest; `edit`/`reproduce` never modify it.
2. **Evidence never mirrors generation targets**: resource `path`
   attributes are places the consumer must *write*, in every profile. There
   is no requirement that evidence contain those files. What evidence must contain is
   whatever the bundle's checks reference (screenshots for L3); a missing
   check reference makes that check `skipped`, never the bundle invalid.
3. For web sources a full bundle's evidence should include: crawled HTML,
   all first-party assets, `network.har`, at least one screenshot, and
   (recommended) a post-JS rendered DOM snapshot (`rendered.html`) —
   required for any resource with `dom_ref_source: rendered`.
4. **Images are generated, never copied**: each image resource must
   carry enough to generate it — `description`, a `model` hint, its
   `requirements/*.md` (composition, subjects, usage constraints), and dom
   context. Consumers synthesize via their image adapter; if no provider is
   available they must stop and surface that, never substitute placeholders
   or reach into evidence.

## 6. digests/

Deterministic projections of evidence, shipped for convenience, regenerable
by any tool implementing the pinned algorithm. Known digests:

- `dom-outline.json` — `{source, nodes: [{selector, tag, id?, classes?, src?, href?, type?}]}`;
  node array order defines `dom_position`.
- `design-tokens.json` — `{colors: {name: {hex, css_variable?, description?}}, fonts: {name: {family, weight}}}`.
- `symbol-map.json` — `{language, module, packages: [{name, files, imports, symbols: [{file, func, params, returns}]}]}`.

## 7. checks.json

```json
{
  "spec": "kitcut-checks/1.0.0-draft",
  "L1_build":      [ {"run": "...", "expect": "exit 0"} | {"check": "files_exist", ...} ],
  "L2_structural": [ Check... ],
  "L2_structural_order": [ {"check": "section_order", "expect": [...], ...} ],
  "L3_visual":     [ {"check": "screenshot_similarity", "reference": "evidence/...", "judge": "llm"} ],
  "L4_acceptance": [ {"judge": "llm", "against": "requirements/<name>.md"} ]
}
```

- **Traceability rule** (normative): every L1–L3 assertion must be derivable
  from facts + evidence (a token hex, a dom_ref, a HAR host, a stdout capture).
  An assertion with no traceable source is invalid — this prevents checks
  from becoming a second prose-truth layer. L4 may reference requirements
  only.
- Known L2 check kinds: `binary_stdout`, `symbol_exists`,
  `test_asserts_literal`, `no_external_deps`, `color_tokens_present`,
  `font_families_loaded`, `dom_refs_resolve`, `cta_scroll_target`,
  `external_hosts_subset`, `form_no_real_submit`, `section_order`,
  `files_exist`, `html_parses`.
- Executor contract: L1/L2 are executed deterministically by the consumer's
  reader (`kit.py verify`) and gate with exit codes; L3/L4 are emitted as
  structured items for a model to judge.
- **L3 availability**: an L3 item whose `reference` does not exist in
  the bundle (distribution profile, or incomplete evidence) is emitted with
  `"skipped": "reference unavailable"` and does not gate. Producers building
  distribution bundles should omit evidence-referencing L3 items entirely.
- **files_exist completeness**: the compiled L1 `files_exist` must list every
  file-resource `path` (pages, stylesheets, images) — the element-level
  `dom_refs_resolve` check does not prove the binary exists on disk.

## 8. Lockfile `.kit-lock.json` (consumer-side, lives in the target dir)

```json
{
  "spec": "kitcut-lock/1.0.0-draft",
  "artifact": {"path": "...", "facts_hash": "sha256:..."},
  "units": {
    "<unit id>": {
      "resources": ["<id>", ...],
      "files": {"<relpath>": "sha256:..."},
      "facts_hash": "sha256:<hash of the unit's facts slice>",
      "recorded_at": "ISO-8601"
    }
  }
}
```

Semantics: `plan` diffs current facts against recorded `facts_hash` per unit —
unchanged ⇒ `keep`; changed ⇒ `regenerate`; new ⇒ `create`; recorded but no
longer in facts ⇒ `delete`. File-hash mismatch vs disk ⇒ drift (hand-edited
generated file): report, don't silently clobber.

## 9. Verify rules catalog (artifact-level; run on every load)

| # | Rule | Failure |
|---|---|---|
| V1 | no dangling edges | hard |
| V2 | no orphans: BFS over edges from `root` reaches every resource | hard |
| V4 | prose coverage both directions (§4.4) | hard |
| V5 | no `${` in requirements prose | hard |
| V6 | `animated_by` / `triggers` edges terminate at a resource carrying `dom_ref` | warn (hard once ingest emits components reliably) |
| V7 | `contains` order values dense per parent | warn |
| V8 | `dom_ref_source: rendered` requires `evidence/rendered.html` | warn |
| V9 | linking-imperative lint in prose (`tofulink`, "must link", `tofukit_` type names) | warn |
| V10 | distribution bundles must not ship `views/` (producer-internal projections) | warn |

## 10. Conformance

A **conforming bundle** passes V1–V5 (V3 per profile) and validates against
the schemas. A **conforming consumer** (a) never treats prose as a source of
edges, (b) executes L1/L2 checks exactly as written, (c) records a lockfile,
(d) **never reads evidence during generation** — evidence, when present, is
touched only by verification. Reference fixtures:

- F1 (repo-mode, full profile): `apps/kitcut/test/results/2026-08-17T07-50-44Z-go-helloworld-kitcut-v2-source`
- F2 (web-mode, full profile, migrated): `apps/kitcut/test/results/2026-08-17T07-40-18Z-kitcut-v2-example-source`
- F3 (web-mode, **distribution profile**): `apps/kitcut/test/results/2026-08-17T07-40-18Z-kitcut-v2-example-artifact`
