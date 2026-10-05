#!/usr/bin/env node
// Local Draw.io viewer + an existing Chromium. No Electron or browser download.
import { access, mkdir, readFile, readdir, realpath, rename, rm, writeFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { dirname, join, resolve, delimiter } from 'node:path';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const revision = 'e159fbf1b1446a37dd68e952ac3db7519735e4f4'; // Draw.io 29.0.3
const assetHashes = {
  'viewer-static.min.js': 'f34eb844dea925189697ef3a175b5bb425a4df6900661feda86eabed80f14719',
  'stencils.min.js': '9d7325444e44a15b140fdc95161691e9d0a2994b89ac7695a253842a4bafd49b',
};
const require = createRequire(import.meta.url);
const help = `Usage: node export-png.mjs [options] input.drawio [output.png]
  --scale N       Pixels per diagram unit (default 2)
  --page N        One-based diagram page (default 1)
  --crop          Crop to content instead of the declared page canvas
  --offline       Require the cached viewer; never download it
  --prepare       Cache the pinned viewer without rendering
  --no-sandbox    Disable Chromium sandbox when required by a container
  --help          Show usage
Browser: DRAWIO_CHROMIUM_PATH or CHROME_PATH, then PLAYWRIGHT_BROWSERS_PATH,
then a standard Chromium/Chrome executable. Never uses your interactive profile.`;

async function executable(path) {
  try { await access(path, constants.X_OK); return path; } catch { return null; }
}

async function onPath(name) {
  for (const entry of (process.env.PATH || '').split(delimiter)) {
    const path = await executable(join(entry, name));
    if (path) return path;
  }
}

async function automation() {
  // Reuse the devcell MCP's installed library without hardcoded Nix store hashes.
  const mcp = await onPath('mcp-server-patchright');
  if (mcp) {
    const root = dirname(dirname(await realpath(mcp)));
    const fromMcp = createRequire(join(root, 'lib/node_modules/nix-patchright-mcp-server/package.json'));
    try { return fromMcp('patchright').chromium; } catch (error) {
      if (error.code !== 'MODULE_NOT_FOUND') throw error;
    }
  }
  try { return require('playwright-core').chromium; } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
    throw new Error('No browser automation library. Run npm ci --ignore-scripts in the skill scripts directory.');
  }
}

async function browserPath() {
  const explicit = process.env.DRAWIO_CHROMIUM_PATH || process.env.CHROME_PATH;
  if (explicit) {
    if (await executable(explicit)) return explicit;
    throw new Error(`Browser is not executable: ${explicit}`);
  }
  const bundle = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (bundle && bundle !== '0') {
    for (const entry of (await readdir(bundle)).sort()) {
      if (!/^chromium-\d+$/.test(entry)) continue;
      for (const suffix of ['chrome-linux/chrome', 'chrome-linux64/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium']) {
        const path = await executable(join(bundle, entry, suffix));
        if (path) return path;
      }
    }
  }
  for (const name of ['chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable']) {
    const path = await onPath(name);
    if (path) return path;
  }
  const mac = await executable('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
  if (mac) return mac;
  throw new Error('No existing Chromium found. Set DRAWIO_CHROMIUM_PATH to its executable.');
}

async function cachedAsset(name, offline) {
  const cache = join(process.env.XDG_CACHE_HOME || join(homedir(), '.cache'), 'drawio-diagram', revision);
  const path = join(cache, name);
  let source, downloaded = false;
  try { source = await readFile(path); } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    if (offline) throw new Error('Viewer is not cached. Run export-png.mjs --prepare once with network access.');
    const response = await fetch(`https://raw.githubusercontent.com/jgraph/drawio/${revision}/src/main/webapp/js/${name}`, { signal: AbortSignal.timeout(30000) });
    if (!response.ok) throw new Error(`Viewer download failed: HTTP ${response.status}`);
    source = Buffer.from(await response.arrayBuffer());
    downloaded = true;
  }
  if (createHash('sha256').update(source).digest('hex') !== assetHashes[name]) {
    throw new Error(`Viewer checksum mismatch. Remove ${path} and run --prepare again.`);
  }
  if (downloaded) {
    await mkdir(cache, { recursive: true });
    const temporary = `${path}.${randomUUID()}.tmp`;
    try { await writeFile(temporary, source); await rename(temporary, path); }
    finally { await rm(temporary, { force: true }); }
  }
  return source.toString('utf8');
}

export async function viewerSource(offline = false) {
  return Promise.all(Object.keys(assetHashes).map(name => cachedAsset(name, offline)));
}

export async function exportPng(input, output, { scale = 2, page = 1, crop = false, offline = false, noSandbox = false } = {}) {
  if (!Number.isFinite(scale) || scale <= 0 || scale > 8) throw new Error('Scale must be greater than 0 and at most 8.');
  if (!Number.isInteger(page) || page < 1) throw new Error('Page must be a positive integer.');
  if (resolve(input) === resolve(output)) throw new Error('Input and output must be different files.');
  const xml = await readFile(input, 'utf8');
  const [source, chromium, executablePath] = await Promise.all([viewerSource(offline), automation(), browserPath()]);
  const browser = await chromium.launch({ executablePath, headless: true, chromiumSandbox: !noSandbox,
    args: ['--disable-dev-shm-usage', '--disable-background-networking'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: scale,
      colorScheme: 'light', serviceWorkers: 'block' });
    const blocked = new Set();
    await context.route('**/*', route => {
      const url = route.request().url();
      if (/^(data:|blob:)/.test(url)) return route.continue();
      blocked.add(url);
      return route.abort();
    });
    const tab = await context.newPage();
    tab.setDefaultTimeout(30000);
    await tab.setContent('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:white}#diagram{position:relative;overflow:hidden}</style><div id="diagram"></div>');
    // The viewer starts MathJax unconditionally. Leave it disabled here;
    // diagrams declaring math=1 receive an explicit error below.
    await tab.addScriptTag({ content: 'window.MathJax = {};' });
    for (const content of source) await tab.addScriptTag({ content });
    const render = async ({ xml, page, crop, scale }) => {
      const parse = text => {
        const doc = new DOMParser().parseFromString(text, 'text/xml');
        if (doc.querySelector('parsererror')) throw new Error('Invalid diagram XML.');
        return doc.documentElement;
      };
      let model = parse(xml);
      if (model.nodeName === 'mxfile') {
        const pages = [...model.children].filter(node => node.nodeName === 'diagram');
        if (!pages[page - 1]) throw new Error(`Page ${page} does not exist (${pages.length} pages).`);
        model = pages[page - 1];
      } else if (page !== 1) throw new Error('This file has only one page.');
      if (model.nodeName === 'diagram') model = model.querySelector('mxGraphModel') || parse(Graph.decompress(model.textContent.trim()));
      if (model.nodeName !== 'mxGraphModel' || !model.querySelector('root')) throw new Error('Expected mxGraphModel or mxfile XML.');
      if (model.getAttribute('math') === '1') throw new Error('MathJax diagrams require desktop Draw.io; the minimal viewer does not bundle MathJax.');
      const host = document.getElementById('diagram');
      const graph = new Graph(host);
      graph.setEnabled(false);
      graph.foldingEnabled = false;
      const editor = new Editor(true, null, null, graph);
      editor.setGraphXml(model);
      graph.view.scaleAndTranslate(1, 0, 0);
      await document.fonts.ready;
      const bounds = graph.getGraphBounds();
      if (!Number.isFinite(bounds.width) || bounds.width <= 0 || bounds.height <= 0) throw new Error('Diagram has no visible content.');
      const pageScale = Number(model.getAttribute('pageScale') || 1);
      const pw = Number(model.getAttribute('pageWidth') || 827) * pageScale;
      const ph = Number(model.getAttribute('pageHeight') || 1169) * pageScale;
      const canvas = !crop && model.getAttribute('page') !== '0';
      if (canvas && !(pw > 0 && ph > 0 && Number.isFinite(pw + ph))) throw new Error('Invalid page dimensions.');
      const left = canvas ? Math.min(0, Math.floor(bounds.x / pw) * pw) : Math.floor(bounds.x) - 10;
      const top = canvas ? Math.min(0, Math.floor(bounds.y / ph) * ph) : Math.floor(bounds.y) - 10;
      const right = canvas ? Math.max(pw, Math.ceil((bounds.x + bounds.width) / pw) * pw) : Math.ceil(bounds.x + bounds.width) + 10;
      const bottom = canvas ? Math.max(ph, Math.ceil((bounds.y + bounds.height) / ph) * ph) : Math.ceil(bounds.y + bounds.height) + 10;
      const width = Math.ceil(right - left), height = Math.ceil(bottom - top);
      if (width * scale > 16000 || height * scale > 16000 || width * height * scale * scale > 64000000) throw new Error('PNG exceeds 64 megapixels or 16000 pixels per side; reduce --scale or use --crop.');
      graph.view.scaleAndTranslate(1, -left, -top);
      host.style.width = width + 'px';
      host.style.height = height + 'px';
      host.style.background = graph.background || 'white';
      // Wait for data-URI image decoding before taking the screenshot.
      await Promise.all([...host.querySelectorAll('img, image')].map(async element => {
        const url = element.src || element.getAttribute('href') || element.getAttribute('xlink:href');
        if (!url) return;
        const image = new Image();
        image.src = url;
        await image.decode();
      }));
      await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)));
      return { width, height };
    };
    // Patchright evaluates in an isolated world by default. CDP explicitly uses
    // the page's main world, where the viewer globals were loaded, for both APIs.
    const cdp = await context.newCDPSession(tab);
    const result = await cdp.send('Runtime.evaluate', {
      expression: `(${render.toString()})(${JSON.stringify({ xml, page, crop, scale })})`,
      awaitPromise: true, returnByValue: true, timeout: 30000,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    const dimensions = result.result.value;
    if (blocked.size) throw new Error(`Diagram needs external assets, which are blocked: ${[...blocked].join(', ')}. Embed images as data URIs or use desktop Draw.io.`);
    await tab.setViewportSize(dimensions);
    // Capture first, then write: failed rendering never replaces an existing PNG.
    const png = await tab.screenshot({ type: 'png', clip: { x: 0, y: 0, ...dimensions }, animations: 'disabled' });
    await writeFile(output, png);
    return { ...dimensions, scale, bytes: png.length, browser: executablePath };
  } finally {
    await browser.close();
  }
}

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    scale: { type: 'string' }, page: { type: 'string' }, crop: { type: 'boolean' },
    offline: { type: 'boolean' }, prepare: { type: 'boolean' }, 'no-sandbox': { type: 'boolean' }, help: { type: 'boolean' },
  } });
  if (values.help) return console.log(help);
  if (values.prepare) { await viewerSource(values.offline); return console.log('Pinned Draw.io viewer cached.'); }
  if (positionals.length < 1 || positionals.length > 2) throw new Error(help);
  const input = positionals[0], output = positionals[1] || input.replace(/\.(drawio|xml)$/i, '') + '.png';
  const result = await exportPng(input, output, { scale: Number(values.scale || 2), page: Number(values.page || 1),
    crop: values.crop, offline: values.offline, noSandbox: values['no-sandbox'] });
  console.log(`${output}: ${result.width * result.scale} × ${result.height * result.scale} px, ${result.bytes} bytes`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(`drawio export: ${error.message}`); process.exitCode = 1; });
}
