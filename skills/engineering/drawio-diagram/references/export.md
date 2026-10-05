# Local PNG export

Use `scripts/export-png.mjs` relative to this skill's directory:

```sh
node scripts/export-png.mjs --no-sandbox --scale 3 input.drawio output.png
```

`--no-sandbox` is needed in devcell containers; omit it on hosts where Chromium's sandbox works. No X11, Xvfb, Electron, running MCP server, or browser profile is required. The script launches and closes its own headless browser process.

## Dependencies and first use

- Node 20+ and an existing Chromium/Chrome.
- In devcell, the script reuses the installed Patchright library and the browser under `PLAYWRIGHT_BROWSERS_PATH`. No npm install is needed.
- Elsewhere, run `npm ci --ignore-scripts` in this skill's `scripts/` directory. The pinned `playwright-core` dependency does not download a browser. Set `DRAWIO_CHROMIUM_PATH` or `CHROME_PATH` to an existing executable if auto-discovery cannot find it.
- First use downloads the pinned Draw.io 29.0.3 viewer and stencil bundle, about **10.6 MiB total**, into `$XDG_CACHE_HOME/drawio-diagram` (default `~/.cache/drawio-diagram`). Both files have SHA-256 verification. They are cached resources, not part of the stack or skill repository.

```sh
node scripts/export-png.mjs --prepare
node scripts/export-png.mjs --offline --no-sandbox input.drawio output.png
```

Rendering blocks network requests. The diagram is never sent to the hosted Draw.io editor. Only the two static assets are downloaded during preparation. Use `--offline` to forbid even those downloads.

## Output behavior

- PNG only; the source `.drawio` remains the editable artifact. PNG does **not** contain embedded XML.
- Accepts raw `mxGraphModel`, a `diagram` element, and compressed or uncompressed `mxfile` pages.
- `--page N` selects a one-based page (default 1); an absent page is an error.
- Preserves the declared page canvas by default, extending by whole pages if content overflows. `--crop` uses content bounds with a 10-unit border. Infinite canvases (`page="0"`) are cropped automatically.
- `--scale N` defaults to 2; 3 is useful for visual review. Output is limited to 64 megapixels and 16000 pixels per side; reduce scale for large diagrams.
- Supports standard shapes, AWS stencils, HTML labels and embedded data-URI images. External images/fonts, MathJax and custom assets are not bundled. Unsupported asset requests fail instead of silently producing an incomplete preview. Use desktop Draw.io in `bbb` for those cases or SVG/PDF/XML-embedded export.
- Errors return a nonzero exit code. Rendering failure leaves an existing output file untouched.

## Why this implementation

The [Awesome Copilot drawio skill](https://awesome-copilot.github.com/skill/drawio/) demonstrates the small viewer-plus-existing-browser approach. Its script otherwise prefers desktop Draw.io and downloads an unpinned viewer during export. This helper uses the same official rendering engine, pinned local assets and the stack's existing automation library.

`@redfire/drawio-export` 0.3.5 includes about 31.6 MiB of files and depends on `playwright-firefox`; it would add a different browser. Its predecessor `drawio-export-puppeteer` is archived. The [drawio-embed API](https://deepwiki.com/imaoda/drawio-embed/3-api-reference) and JGraph's `diagram-editor.js` are iframe integration helpers; they require a separate hosted or local editor, so they are not standalone renderers.

## Regression checks

After `--prepare`, run `node --test scripts/export-png.test.mjs`. Set `DRAWIO_TEST_NO_SANDBOX=1` in containers. Tests render the bundled generic/AWS examples and check page dimensions, compressed input, page selection, error exit status and external-asset blocking. They do not validate every stencil or compare every pixel with desktop Draw.io. Inspect the resulting PNGs for visual regressions when changing the renderer version.
