#!/usr/bin/env node
/**
 * filetree.js — Sorted file manifest for a React Native / Expo app
 *
 * Usage:
 *   node filetree.js <path-to-app-root>
 *
 * Output: JSON array of relative file paths to stdout (sorted)
 * Exit code: 0 on success, 1 on error
 */

'use strict';

const fs = require('fs');
const path = require('path');

const SKIP_DIRS = new Set([
  'node_modules', '.git', '.expo', 'ios', 'android',
  'dist', 'build', '.idea', '.vscode', '__pycache__',
  '.venv', 'venv', '.pytest_cache', '.mypy_cache',
  '.turbo', '.next', 'coverage',
]);

const ALLOW_DOTFILES = new Set([
  '.env.example', '.gitignore', '.node-version',
]);

function walk(dir, root, results) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      walk(path.join(dir, entry.name), root, results);
    } else {
      if (entry.name.startsWith('.') && !ALLOW_DOTFILES.has(entry.name)) continue;
      results.push(path.relative(root, path.join(dir, entry.name)).replace(/\\/g, '/'));
    }
  }
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    process.stderr.write('Usage: node filetree.js <path-to-app-root>\n');
    process.exit(1);
  }

  const appRoot = path.resolve(args[0]);
  if (!fs.existsSync(appRoot)) {
    process.stderr.write(`Error: path does not exist: ${appRoot}\n`);
    process.exit(1);
  }

  const results = [];
  walk(appRoot, appRoot, results);
  results.sort();

  process.stdout.write(JSON.stringify(results, null, 2) + '\n');
}

main();
