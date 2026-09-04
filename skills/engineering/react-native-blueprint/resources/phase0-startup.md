# Phase 0: Startup

Get the app running locally before extracting features. Visual verification via Playwright confirms the app is functional before code analysis.

---

## 0.1 Create Taskfile.yml

Every extract project MUST have a `Taskfile.yml` with `install` and `start` tasks that work from ground zero (no pre-existing node_modules).

```yaml
version: '3'

vars:
  APP_DIR: '{{.ROOT_DIR}}/../../.workspaces/<app-name>'

tasks:
  install:
    desc: Install all dependencies including platform extras
    dir: '{{.APP_DIR}}'
    cmds:
      - npm install
      - <platform-specific installs>
    status:
      - test -d node_modules
      - <verify key packages exist>

  start:
    desc: Start app on localhost:<port>
    dir: '{{.APP_DIR}}'
    deps: [install]
    cmds:
      - <start command>
```

---

## 0.2 Expo React Native → Web Dependencies

Mobile-first Expo projects lack web dependencies. Install them explicitly:

```bash
npm install                                              # base deps
npx expo install react-native-web react-dom              # web platform
npx expo install react-native-reanimated                 # if babel.config.js references its plugin
```

**Entrypoint identification:**
1. `package.json` → `main` field or `expo.entryPoint`
2. `app.json` → `expo.plugins` array = native modules that need npm packages
3. `babel.config.js` → `plugins` array = Babel plugins needing their npm packages installed
4. `app/` directory → expo-router auto-loads ALL route files; any import error in ANY file crashes the app

---

## 0.3 Iterative Startup with Playwright Debugging

Start the server, then use Playwright CDP to diagnose errors:

```
1. Start server in background → check Metro output for build errors
2. browser_navigate to localhost → load page
3. browser_console_messages level=error → read JS errors
4. browser_snapshot → read error overlay (shows file + line)
5. browser_take_screenshot → visual confirmation
6. Fix error → repeat from step 2
```

---

## 0.4 Common Errors & Fixes

| Console Error | Root Cause | Fix |
|--------------|-----------|-----|
| `Cannot find module 'X/plugin'` | Babel plugin package missing | `npx expo install X` |
| `Cannot use 'import.meta' outside a module` | Hermes outputs `import.meta` but script tag lacks `type="module"` | Patch `node_modules/expo/node_modules/@expo/cli/build/src/export/html.js`: change `defer></script>` to `defer type="module"></script>` |
| `Cannot access 'X' before initialization` | TDZ: `const` used before declaration | Move const declaration before its usage |
| `don't have the required dependencies` | Missing web platform packages | `npx expo install react-native-web react-dom` |
| `Error: The given URL has an empty path` | HMR + `type="module"` conflict (`jsc-safe-url`) | Use `--no-dev` flag to disable HMR |

---

## 0.5 Expo SDK 54+ Web Quirks

- **Hermes is mandatory for web** — `transform.engine=hermes` is forced, cannot be disabled
- **`type="module"` patch required** — Hermes outputs `import.meta.env` but Expo serves `<script defer>` without module type
- **HMR crashes with `type="module"`** — Use `--no-dev` for stable web serving
- **`@expo/webpack-config` is dead** — Expo 54 uses Metro for web; don't install webpack-config (peer dep conflict)
- **File to patch:** `node_modules/expo/node_modules/@expo/cli/build/src/export/html.js` (function `appendScriptsToHtml`)
- **Add `patch-web` task** to Taskfile.yml with `sed` + `status` check so it's idempotent

---

## Quality Check

- [ ] App loads without JS errors in browser console
- [ ] Main tab bar visible and navigable
- [ ] At least one screen renders content (not blank)
- [ ] Playwright can take a screenshot confirming visual render
