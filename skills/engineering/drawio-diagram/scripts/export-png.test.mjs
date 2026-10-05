// L1: real offline rendering with the installed Chromium and library. No image
// rebuild. --prepare must run once. Uses the same discovery/flags as the CLI.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { deflateRawSync } from 'node:zlib';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { exportPng, viewerSource } from './export-png.mjs';

const options = { offline: true, scale: 1, noSandbox: process.env.DRAWIO_TEST_NO_SANDBOX === '1' };
const model = (width = 400, label = 'Hello') => `<mxGraphModel page="1" pageWidth="${width}" pageHeight="300"><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" value="${label}" style="rounded=1;html=1;fillColor=#ff0000" vertex="1" parent="1"><mxGeometry x="30" y="40" width="120" height="60" as="geometry"/></mxCell></root></mxGraphModel>`;
async function fixture(run) {
  const directory = await mkdtemp(join(tmpdir(), 'drawio-skill-test-'));
  try { await run(directory); } finally { await rm(directory, { recursive: true, force: true }); }
}
async function dimensions(path) {
  const png = await readFile(path);
  assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]);
  assert.ok(png.length > 1000, 'nontrivial rendered PNG');
  return [png.readUInt32BE(16), png.readUInt32BE(20)];
}

for (const [example, size] of [['generic', [1169, 827]], ['aws', [1400, 1000]]]) {
  test(`offline ${example} example preserves the complete canvas beyond the initial viewport`, () => fixture(async directory => {
    const input = fileURLToPath(new URL(`../references/examples/example-${example}.drawio`, import.meta.url));
    const output = join(directory, 'out.png');
    await exportPng(input, output, options);
    assert.deepEqual(await dimensions(output), size);
  }));
}

test('compressed second page, HTML label and scale', () => fixture(async directory => {
  const compressed = deflateRawSync(encodeURIComponent(model(500, '&lt;b&gt;Hello&lt;/b&gt; &amp; 世界'))).toString('base64');
  const input = join(directory, 'input.drawio'), output = join(directory, 'out.png');
  await writeFile(input, `<mxfile><diagram>${model()}</diagram><diagram>${compressed}</diagram></mxfile>`);
  await exportPng(input, output, { ...options, page: 2, scale: 2 });
  assert.deepEqual(await dimensions(output), [1000, 600]);
}));

test('crop uses content bounds', () => fixture(async directory => {
  const input = join(directory, 'input.drawio'), output = join(directory, 'out.png');
  await writeFile(input, model());
  await exportPng(input, output, { ...options, crop: true });
  const [width, height] = await dimensions(output);
  assert.ok(width >= 140 && width <= 145 && height >= 80 && height <= 85);
}));

test('invalid XML and nonexistent page fail without overwriting the output', () => fixture(async directory => {
  const input = join(directory, 'input.drawio'), output = join(directory, 'out.png');
  await writeFile(output, 'preserve me');
  await writeFile(input, '<mxfile>broken');
  await assert.rejects(exportPng(input, output, options), /Invalid diagram XML/);
  await writeFile(input, model());
  await assert.rejects(exportPng(input, output, { ...options, page: 2 }), /only one page/);
  assert.equal(await readFile(output, 'utf8'), 'preserve me');
}));

test('external images cannot silently produce incomplete PNGs', () => fixture(async directory => {
  const input = join(directory, 'input.drawio'), output = join(directory, 'out.png');
  await writeFile(input, model().replace('rounded=1;', 'shape=image;image=https://example.invalid/image.png;'));
  await assert.rejects(exportPng(input, output, options), /external assets|source image cannot be decoded/);
  await assert.rejects(readFile(output), { code: 'ENOENT' });
}));

test('bad arguments and missing input exit nonzero', () => fixture(async directory => {
  const cli = fileURLToPath(new URL('./export-png.mjs', import.meta.url));
  for (const args of [[], ['--scale', '0', 'x.drawio'], [join(directory, 'missing.drawio')]]) {
    const result = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', timeout: 5000 });
    assert.equal(result.status, 1, result.stderr);
  }
}));

test('offline mode fails on missing or corrupted cached assets', () => fixture(async directory => {
  const previous = process.env.XDG_CACHE_HOME;
  process.env.XDG_CACHE_HOME = directory;
  try {
    await assert.rejects(viewerSource(true), /not cached/);
    const cache = join(directory, 'drawio-diagram/e159fbf1b1446a37dd68e952ac3db7519735e4f4');
    await mkdir(cache, { recursive: true });
    for (const name of ['viewer-static.min.js', 'stencils.min.js']) await writeFile(join(cache, name), 'tampered');
    await assert.rejects(viewerSource(true), /checksum mismatch/);
  } finally {
    if (previous === undefined) delete process.env.XDG_CACHE_HOME;
    else process.env.XDG_CACHE_HOME = previous;
  }
}));
