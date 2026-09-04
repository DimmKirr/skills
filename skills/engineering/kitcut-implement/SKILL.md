---
name: kitcut-implement
description: Reproduce a working application from a kitcut-artifact/2.0 bundle (facts.json + checks.json + requirements/ + digests/; evidence/ optional and verification-only). Use when the user provides an artifact bundle directory and wants the described app rebuilt, reproduced, implemented, or incrementally re-applied after an edit to the bundle. Do NOT use for analyzing/reviewing ordinary source repos or for creating artifacts (that is ingest's job).
argument-hint: <artifact-dir> [target-dir]
---

# kitcut-implement

Reproduce the application described by an artifact bundle into a target
directory, unit by unit, gated by the bundle's own checks. The bundle is the
only source of truth: [references/artifact-spec.md](references/artifact-spec.md).

Two hard rules before anything else:

1. **Never read `evidence/` during generation — for anything, ever.**
   Distribution bundles have no `evidence/` at all; when a full bundle has
   one, it exists solely for verification (L3 references). Generation works
   from `facts.json`, `requirements/`, and `digests/` — no exceptions, no
   copying, including image binaries.
2. **Everything deterministic goes through the reader.** You never parse
   facts.json yourself, never compute the plan yourself, never decide
   verification passed yourself — `scripts/kit.py` does, and its exit codes
   gate you.

## Obtaining the artifact bundle

Bundles live in the workspace git repo produced by `kitcut export`. To clone remotely:

```bash
kitcut serve --data-root ./data/kitcut --token <secret> --addr :8090
git -c "http.extraHeader=Authorization: Bearer <secret>" \
  clone http://localhost:8090/local/<project>.git
```

The `.kitcut/artifact/` directory inside the clone is the bundle. Alternatively, use a local worktree:

```bash
git --git-dir=<git_repo> worktree add .worktrees/<workspace> HEAD
```

## Transport

| Verb | Command |
|---|---|
| plan | `python3 scripts/kit.py plan <artifact> --target <dir>` |
| next | `python3 scripts/kit.py next <artifact> --target <dir>` |
| record | `python3 scripts/kit.py record <artifact> --target <dir> --unit <id> --files <f1> <f2> ...` |
| verify | `python3 scripts/kit.py verify <artifact> --target <dir>` |
| image | `python3 scripts/genimage.py --prompt "..." --out <path>` (only when evidence lacks the asset) |

Run from the skill directory (paths above are skill-relative). If the bundle
is invalid, every command exits 2 with the violated rule (V1–V5) — report it
and stop; a broken artifact is the producer's bug, not yours to patch.

## The loop

```
1. plan        → {create, regenerate, keep, delete, drift}
                 - delete: remove those units' files listed in the lockfile
                 - drift: a generated file was hand-edited; report it and ask
                   before overwriting — never silently clobber
2. next        → context package for the first unbuilt unit, or {"done": true}
3. generate    → YOU write the unit's files into the target, using ONLY the
                 package: resources + edges (what exists, what it relates to,
                 in what order), requirements (observed behavior + intent),
                 digests (tokens, symbols, DOM outline), dep_interfaces
                 (names/paths/hashes of already-built units — never their source)
4. record      → lockfile entry for the unit (list every file you wrote)
5. goto 2 until done
6. verify      → L1/L2 executed by the reader; L3_items/L4_items returned for
                 YOU to judge (see Verification)
7. on failure  → regenerate the failing unit(s) from the check's evidence,
                 record, re-verify. Never hand-patch outside the loop, never
                 claim success while any L1/L2 check fails.
```

Progress report after each unit: `unit N/M recorded: <id>`.

## Generation guidance (step 3)

- Respect **structural order**: `contains` edges carry `attributes.order`;
  assemble parents from children in that order. Document order of anchored
  elements is `dom_position` (sort key only).
- Respect **roles**: `implemented_by` says which file realizes a feature;
  `styled_by`/`uses_font` say which tokens to use (values in
  `digests/design-tokens.json`); `triggers`/`navigates_to` are behavior you
  must wire (a CTA that scrolls to its target, etc.).
- Requirements prose is declarative observation, not instructions to link —
  backticked names in prose carry no semantic weight; the edges do.
- Match the target's conventions implied by facts (`written_in`, libraries
  with versions). Scaffold files (module manifests, lockfiles) belong to the
  `scaffold` unit.
- **Token/concept units may own zero files** (colors, fonts, animations are
  realized inside a stylesheet or page owned by a later unit). Record them
  with an empty `--files` list — the lockfile still tracks their facts hash,
  so edits to them correctly mark the unit for regeneration.

## Images

**Every image is generated, never copied.** For each image resource, compose
the generation prompt from its `description` attribute + its
`requirements/*.md` (subjects, composition, usage constraints like "calm
center for text overlay") + dom context (hero background vs inline product
shot), honor the resource's `model` hint, and produce it with
`scripts/genimage.py --prompt "..." --out <target>/<path>`. Size from usage:
hero/background wide (e.g. 1536x1024), inline content square-ish.

If no provider is configured (`KIT_IMAGE_PROVIDER` + key), the script exits 3
with "provider unavailable" — **stop and surface that to the user**. Never
substitute placeholders, and never fall back to evidence binaries even if a
full bundle happens to contain them.

### Review feedback loop (every image, every run)

`genimage.py` is transport; **you are the validator, and you drive the
loop** (the inverse of tofukit's `svg_executor`, where the harness validates
and the LLM regenerates — here the provider generates and the LLM judges):

1. **Generate** the image (transport per mode below).
2. **Review**: Read the produced image and judge it against
   (a) the resource's `requirements/*.md` Visual Requirements and
   Constraints — mandated subjects, composition zones ("calm center for
   text overlay"), palette, style; and (b) **cross-image consistency** —
   shared character design, rendering style (flat vector vs 3D render),
   and palette across the whole image set. List concrete violations.
3. **Pass** → accept. **Fail** → regenerate with a `REVIEW FEEDBACK`
   block appended to the original prompt: each named violation and what
   must change. Provider errors (e.g. `moderation_blocked`) count as
   failed attempts — retry, adjusting the prompt only if the error names
   a cause.
4. **Max 3 attempts per image.** After that keep the best attempt and
   report the unresolved violations — never silently accept, never claim
   the image passed review.

The run report includes a per-image verdict line (pass/fail + reason).
An image unit is recorded only after its images have been reviewed.

### Debug mode (`DEBUG=true`)

When the env has `DEBUG=true` (or the user asks for a debug run), **never
call `scripts/genimage.py`** — no paid provider is invoked. Instead, for
each image compose the same generation prompt, then author an SVG wireframe
yourself (Inkscape MCP or hand-written SVG: composition zones, subject
silhouettes, palette from `digests/design-tokens.json`, a visible `DEBUG`
watermark) and rasterize it at the size a real run would use. The same
review feedback loop applies to the wireframes.

All debug artifacts — per-attempt prompt, SVG source, raster, review
verdict — live under
`.scratch/debug/<projectName>/<dateTimeISO>-<testNameInfo>-<id>/`
(projectName from the artifact's meta, testNameInfo = unit or run label,
id = short unique suffix). Copy the final raster to the resource's target
path so the page renders. Debug images are structural stand-ins, not
deliverables: report the run as a debug build, treat every L3 visual check
touching a debug image as `skipped: debug image`, and never claim
completion until a real-provider run replaces them.

## Verification (step 6)

- `verify` exit 0 = L1/L2 green. Exit 1 = failures listed with `actual`
  evidence — regenerate, don't rationalize.
- **L3_items** (visual): render/screenshot the target where applicable and
  judge against the referenced evidence screenshot yourself. Items marked
  `"skipped": "reference unavailable"` (distribution bundles) are reported
  as skipped, not judged and not failed.
- **L4_items** (acceptance): read the referenced requirements file and judge
  whether the generated unit satisfies the observed behavior and intent.
  Report each item pass/fail with one line of evidence.
- Completion claim requires: verify exit 0 AND your L3/L4 judgments pass AND
  the lockfile covers every planned unit. Anything less is reported as
  incomplete, with what remains.

## Incremental applies (edited bundles)

Re-running on a previously reproduced target is the normal path, not a
special case: `plan` returns `keep` for unchanged units (do zero work for
them), `regenerate` for units whose facts changed, `delete` for removed ones.
Trust the plan — do not rebuild kept units "to be safe".
