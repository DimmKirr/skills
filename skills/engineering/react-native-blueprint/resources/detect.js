#!/usr/bin/env node
/**
 * detect.js — Deterministic React Native / Expo app scanner
 *
 * Usage:
 *   node detect.js <path-to-app-root>
 *
 * Output: JSON to stdout
 * Errors/warnings: stderr
 * Exit code: 0 on success, 1 on error
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ─── Helpers ────────────────────────────────────────────────────────────────

function warn(msg) {
  process.stderr.write(`[detect] warn: ${msg}\n`);
}

/** Glob a directory recursively for files matching an extension list. */
function glob(dir, extensions) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  function walk(current) {
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (extensions.some(ext => entry.name.endsWith(ext))) {
        results.push(full);
      }
    }
  }

  walk(dir);
  return results;
}

/** Read file contents, return null on error. */
function readFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }
}

/** Relative path from appRoot, normalised with forward slashes. */
function rel(appRoot, absPath) {
  return path.relative(appRoot, absPath).replace(/\\/g, '/');
}

/** Basename without extension. */
function baseName(filePath) {
  return path.basename(filePath, path.extname(filePath));
}

// ─── Tech Detection ─────────────────────────────────────────────────────────

function detectTech(appRoot) {
  const pkgPath = path.join(appRoot, 'package.json');
  const raw = readFile(pkgPath);
  if (!raw) {
    warn('package.json not found — tech detection skipped');
    return {};
  }

  let pkg;
  try {
    pkg = JSON.parse(raw);
  } catch (e) {
    warn(`package.json parse error: ${e.message}`);
    return {};
  }

  const deps = {
    ...pkg.dependencies,
    ...pkg.devDependencies,
  };

  const tech = {};

  // Framework
  if (deps['react-native'] !== undefined) {
    tech.framework = 'react-native';
    tech.framework_version = deps['react-native'];
  }

  // Expo SDK
  if (deps['expo'] !== undefined) {
    tech.expo_sdk = deps['expo'];
  }

  // Navigation
  if (deps['expo-router'] !== undefined) {
    tech.navigation = 'expo-router';
  } else {
    const reactNavKeys = Object.keys(deps).filter(k =>
      k.startsWith('@react-navigation/')
    );
    if (reactNavKeys.length > 0) {
      tech.navigation = 'react-navigation';
    }
  }

  // State management
  if (deps['zustand'] !== undefined) {
    tech.state = 'zustand';
  } else if (
    deps['redux'] !== undefined ||
    deps['@reduxjs/toolkit'] !== undefined
  ) {
    tech.state = 'redux';
  } else if (deps['jotai'] !== undefined) {
    tech.state = 'jotai';
  } else if (deps['recoil'] !== undefined) {
    tech.state = 'recoil';
  } else if (deps['mobx'] !== undefined || deps['mobx-react'] !== undefined) {
    tech.state = 'mobx';
  }

  // API client
  if (deps['axios'] !== undefined) {
    tech.api_client = 'axios';
  } else if (deps['@tanstack/react-query'] !== undefined) {
    tech.api_client = 'react-query';
  } else if (deps['swr'] !== undefined) {
    tech.api_client = 'swr';
  }

  // Icons
  if (deps['@expo/vector-icons'] !== undefined) {
    tech.icon_lib = '@expo/vector-icons';
  } else if (deps['react-native-vector-icons'] !== undefined) {
    tech.icon_lib = 'react-native-vector-icons';
  }

  // Animation
  if (deps['react-native-reanimated'] !== undefined) {
    tech.animation_lib = 'react-native-reanimated';
  } else if (deps['react-native-animatable'] !== undefined) {
    tech.animation_lib = 'react-native-animatable';
  }

  // Realtime
  tech.realtime =
    deps['socket.io-client'] !== undefined ||
    deps['@supabase/realtime-js'] !== undefined;

  // IAP
  tech.iap = deps['react-native-purchases'] !== undefined;

  // Error tracking
  if (deps['@sentry/react-native'] !== undefined) {
    tech.error_tracking = 'sentry';
  } else if (deps['@bugsnag/react-native'] !== undefined) {
    tech.error_tracking = 'bugsnag';
  }

  return tech;
}

// ─── Screen Inventory ────────────────────────────────────────────────────────

/**
 * Convert a file path (relative to app/) to a route string.
 * e.g. "(tabs)/index.tsx" → "/(tabs)/index"
 */
function fileToRoute(relToApp) {
  // Strip extension
  let route = relToApp.replace(/\.[jt]sx?$/, '');
  // Convert OS separators
  route = route.replace(/\\/g, '/');
  // Add leading slash
  if (!route.startsWith('/')) route = '/' + route;
  // Strip trailing /index → keep / for root
  route = route.replace(/\/index$/, '') || '/';
  return route;
}

function detectScreens(appRoot) {
  const appDir = path.join(appRoot, 'app');
  if (!fs.existsSync(appDir)) return [];

  const tsxFiles = glob(appDir, ['.tsx', '.jsx', '.ts', '.js']);

  const screens = [];
  for (const file of tsxFiles) {
    const relToApp = path.relative(appDir, file).replace(/\\/g, '/');
    const base = path.basename(relToApp);

    // Skip layout and special files
    if (
      base.endsWith('_layout.tsx') ||
      base.endsWith('_layout.jsx') ||
      base.endsWith('_layout.ts') ||
      base.endsWith('_layout.js') ||
      base === '+not-found.tsx' ||
      base === '+not-found.jsx' ||
      base.startsWith('+')
    ) {
      continue;
    }

    const dir = path.dirname(relToApp);
    const groupMatch = dir.match(/\(([^)]+)\)/);
    const group = groupMatch ? `(${groupMatch[1]})` : (dir === '.' ? '' : dir);
    const isTab = group === '(tabs)';
    const route = fileToRoute(relToApp);

    screens.push({
      route,
      file: `app/${relToApp}`,
      group: group || null,
      isTab,
    });
  }

  // Sort deterministically
  screens.sort((a, b) => a.route.localeCompare(b.route));
  return screens;
}

// ─── API Discovery ───────────────────────────────────────────────────────────

const HTTP_METHOD_RE =
  /(?:axios\.|fetch\s*\(|api\.)?(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`\n]+)['"`]/gi;

const AXIOS_BASE_URL_RE = /baseURL\s*:\s*['"`]([^'"`\n]+)['"`]/i;

const FETCH_RE =
  /fetch\s*\(\s*(?:BASE_URL\s*\+\s*)?['"`]([^'"`\n]+)['"`]\s*,\s*\{[^}]*method\s*:\s*['"`](GET|POST|PUT|DELETE|PATCH)['"`]/gi;

function detectApiEndpoints(appRoot) {
  const searchDirs = [
    path.join(appRoot, 'src', 'services'),
    path.join(appRoot, 'src', 'api'),
    path.join(appRoot, 'services'),
    path.join(appRoot, 'api'),
    path.join(appRoot, 'lib'),
  ];

  const endpoints = [];

  for (const dir of searchDirs) {
    if (!fs.existsSync(dir)) continue;
    const files = glob(dir, ['.ts', '.js', '.tsx', '.jsx']);

    for (const file of files) {
      const content = readFile(file);
      if (!content) continue;

      const relFile = rel(appRoot, file);

      // Match axios-style: .get('/path'), .post('/path')
      let m;
      const re1 = new RegExp(HTTP_METHOD_RE.source, 'gi');
      while ((m = re1.exec(content)) !== null) {
        endpoints.push({
          method: m[1].toUpperCase(),
          path: m[2],
          source: relFile,
        });
      }

      // Match fetch-style: fetch('/path', { method: 'GET' })
      const re2 = new RegExp(FETCH_RE.source, 'gi');
      while ((m = re2.exec(content)) !== null) {
        endpoints.push({
          method: m[2].toUpperCase(),
          path: m[1],
          source: relFile,
        });
      }
    }
  }

  // Also check for openapi/swagger files
  const openapiCandidates = [
    'openapi.json',
    'swagger.json',
    'openapi.yaml',
    'swagger.yaml',
  ];
  for (const candidate of openapiCandidates) {
    const p = path.join(appRoot, candidate);
    if (fs.existsSync(p)) {
      endpoints.push({
        method: '__openapi__',
        path: candidate,
        source: candidate,
      });
    }
  }

  // Deduplicate (same method+path+source)
  const seen = new Set();
  return endpoints.filter(e => {
    const key = `${e.method}:${e.path}:${e.source}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ─── Store Inventory ─────────────────────────────────────────────────────────

function detectStores(appRoot) {
  const storeDir = path.join(appRoot, 'src', 'stores');
  if (!fs.existsSync(storeDir)) return [];

  const files = glob(storeDir, ['.ts', '.js', '.tsx', '.jsx']);
  return files.map(f => ({
    file: rel(appRoot, f),
    name: baseName(f),
  })).sort((a, b) => a.name.localeCompare(b.name));
}

// ─── Component Inventory ─────────────────────────────────────────────────────

function detectComponents(appRoot) {
  const searchDirs = [
    path.join(appRoot, 'src', 'components'),
    path.join(appRoot, 'components'),
    path.join(appRoot, 'lib', 'components'),
  ];

  const components = [];
  const seen = new Set();

  for (const dir of searchDirs) {
    if (!fs.existsSync(dir)) continue;
    // Only top-level files (not recursive sub-dirs) per spec
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (entry.isDirectory()) continue;
      if (!/\.[jt]sx?$/.test(entry.name)) continue;
      const full = path.join(dir, entry.name);
      const name = baseName(full);
      if (seen.has(name)) continue;
      seen.add(name);
      components.push({
        file: rel(appRoot, full),
        name,
      });
    }
  }

  components.sort((a, b) => a.name.localeCompare(b.name));
  return components;
}

// ─── Asset Inventory ─────────────────────────────────────────────────────────

function detectAssets(appRoot) {
  const assetsDir = path.join(appRoot, 'assets');

  const imageExts = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp'];
  const fontExts = ['.ttf', '.otf'];

  const images = [];
  const icons = [];
  const fonts = [];

  if (fs.existsSync(assetsDir)) {
    // Images: all image files under assets/, excluding icons/ and fonts/
    const allFiles = glob(assetsDir, [...imageExts, ...fontExts]);

    for (const file of allFiles) {
      const relPath = rel(appRoot, file);
      const ext = path.extname(file).toLowerCase();

      if (fontExts.includes(ext)) {
        fonts.push(relPath);
        continue;
      }

      if (imageExts.includes(ext)) {
        // icons/ sub-directory
        const parts = relPath.replace(/\\/g, '/').split('/');
        if (parts.includes('icons')) {
          icons.push(relPath);
        } else {
          images.push(relPath);
        }
      }
    }
  }

  images.sort();
  icons.sort();
  fonts.sort();

  return {
    images,
    icons,
    fonts,
    total_count: images.length + icons.length + fonts.length,
  };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    process.stderr.write(
      'Usage: node detect.js <path-to-react-native-app-root>\n'
    );
    process.exit(1);
  }

  const appRoot = path.resolve(args[0]);

  if (!fs.existsSync(appRoot)) {
    process.stderr.write(`Error: path does not exist: ${appRoot}\n`);
    process.exit(1);
  }

  const result = {
    tech: detectTech(appRoot),
    screens: detectScreens(appRoot),
    api_endpoints: detectApiEndpoints(appRoot),
    stores: detectStores(appRoot),
    components: detectComponents(appRoot),
    assets: detectAssets(appRoot),
  };

  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}

main();
