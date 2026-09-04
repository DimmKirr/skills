# MCP & Browser Stealth Testing — Domain Reference

> Examples reference [DevCell](https://github.com/devcell-sh/devcell) paths and modules (`managed-mcp.nix`, `patchright-mcp-cell`, `/opt/npm-tools`). Adapt to your container setup.

## Cost Table

| Level | Gate | Execute | Cost | Proves |
|-------|------|---------|------|--------|
| L1 | `node --check stealth-init.dev.js` | `node webgl-proxy-test.js` (narrowest) or `node bot-detect-test.js` (full suite) | 5s–60s | Init-script stealth: WebGL spoofing, bot detection scores |
| L2 | `nix-instantiate --parse managed-mcp.nix` | `nix build .#patchright-mcp-cell` + run wrapper | ~5min | Nix wrapper bundles correct init-script and flags at expected path |
| L3 | Dockerfile lint | `task image:build` + container + MCP | ~30min | Full pipeline: image builds, entrypoint works, MCP stdio, secrets resolution |

## Contract Surface: Bot Detection

The contract surface between isolated testing and the full MCP pipeline:

```
chromium --no-sandbox \
         --use-gl=angle \
         --use-angle=swiftshader \
         --enable-unsafe-swiftshader \
         --ozone-platform=headless \
         --ozone-override-screen-size=1920,1080 \
         --window-size=1920,1080 \
         --force-device-scale-factor=1 \
         --disable-features=AudioServiceSandbox \
         --autoplay-policy=no-user-gesture-required
+ stealth-init.js (init-script injected via context.addInitScript)
```

**Key insight:** Both `bot-detect-test.js` and `patchright-mcp-cell` use the same `CHROME_ARGS` array and init-script. If the isolated test passes, the same behavior occurs in the MCP pipeline — the contract surface is identical.

## Example: Iterating on Init-Script Stealth

**Scenario:** CreepJS reports 36% "like headless" — need to improve stealth.

**Wrong approach (30min/iteration):**
1. Edit init-script in nix module
2. `task image:build` (30min)
3. Restart container, reconnect Claude Code MCP
4. Ask MCP to navigate to creepjs
5. Wait for results, discover caching issues
6. Repeat

**Right approach (30s/iteration):**
1. Copy init-script locally: `stealth-init.dev.js`
2. Edit the script
3. `node test/bot-detect-test.js --init-script ./stealth-init.dev.js --only creepjs` (30s)
4. Read structured JSON output
5. Iterate until scores improve
6. **Then** integrate into nix module and level up to L2

**Boundary documentation for this test:**

```
This test proves:
  - Patchright + chrome flags + init-script achieve target bot detection scores
  - WebGL spoofing, navigator overrides, and fingerprint masking work correctly

This test does NOT prove:
  - Nix can build the wrapper with the updated init-script
  - The init-script is correctly bundled at the expected path in the nix store
  - MCP stdio protocol correctly starts/stops the browser
  - Entrypoint correctly sets up DISPLAY, fluxbox, X11 for the container

Environment assumptions:
  - DISPLAY is set and X11/Xvfb is running
  - Fluxbox or window manager is active
  - /opt/npm-tools/node_modules/patchright is installed
  - SwiftShader libraries are available

Contract surface match: IDENTICAL
  - Chrome args: same array as patchright-mcp-cell
  - Init-script: same file (or local dev copy with same content)
```

## Example: Testing WebGL Proxy in Isolation (L1 — narrowest scope)

**Scenario:** Need to verify that the init-script correctly intercepts WebGL context and spoofs GPU parameters.

```bash
# L1 gate: syntax check
node --check test/webgl-proxy-test.js

# L1 execute: just the proxy mechanism (~5s)
node test/webgl-proxy-test.js
# Output: { vendor: "SPOOFED_VENDOR", renderer: "SPOOFED_RENDERER", hasExt: true, ... }
```

**Widen scope within L1:** If the proxy test passes but bot detectors still flag WebGL, the issue is in how the spoofed values interact with fingerprinting heuristics (canvas hash, readPixels consistency) — run the full bot detection suite at L1: `node bot-detect-test.js`.

## Level-Up Decision Tree

```
Init-script change?
  ├─ Only JS logic (spoofing, overrides) → Start at L1 (webgl-proxy-test, narrowest scope)
  │   └─ L1 narrow passes → widen L1 (bot-detect-test) → scores good? → STOP
  │                                                     → scores bad?  → iterate at L1
  ├─ Chrome flags change → Start at L1 (bot-detect-test, contract surface changed)
  ├─ Nix wrapper change (paths, bundling) → Start at L2 (gate: nix-instantiate --parse, execute: nix build)
  └─ Entrypoint/image change → L3 required (gate: dockerfile lint, execute: task image:build)
```
