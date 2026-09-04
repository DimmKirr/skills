# Worked Examples

### Example 1: Patchright Bot Detection (MCP domain)

**Task:** Verify patchright MCP passes bot detection after init-script changes.

**Concern boundary analysis:**
```
Full pipeline: nix module → nix build → docker image → entrypoint → MCP stdio → chromium + init-script → page
                                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^
                                                                                  Contract surface identified
```

**Pyramid cascade:**

| Level | Gate | Execute | Cost | What it proves | What it assumes |
|-------|------|---------|------|----------------|-----------------|
| L1 | `node --check stealth-init.dev.js` | `node bot-detect-test.js --init-script ./stealth-init.dev.js` | 30s | Full stealth passes 3 bot detectors | patchright installed, DISPLAY set, swiftshader libs present |
| L2 | `nix-instantiate --parse managed-mcp.nix` | `nix build .#patchright-mcp-cell && ./result/bin/patchright-mcp-cell` | 5min | Nix wrapper bundles init-script at correct path | Assumes L1 stealth logic works |
| L3 | Dockerfile lint | `task image:build` + container restart + MCP reconnect | 30min | Full integrated pipeline | Assumes L1-L2 all work |

**Decision:** Start at L1. The init-script change is JS-only, contract surface (chrome args) didn't change. Run `bot-detect-test.js` 10 times to iterate. Level up to L2 only after scores are satisfactory.

**Result:** 10 iterations at L1 = 5 minutes total. Same work at L3 = 5 hours.

### Example 2: Adding a Nix Package (nix domain)

**Task:** Add `wokwi-cli` to `electronics.nix`.

**Concern boundary analysis:**
```
Full pipeline: edit .nix → nix eval (syntax) → nix build (derivation) → docker image → entrypoint → binary available
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
               Can validate most of this without docker
```

**Pyramid cascade:**

| Level | Gate | Execute | Cost | What it proves | What it assumes |
|-------|------|---------|------|----------------|-----------------|
| L1 | `task nix:validate` (syntax + attr check) | `nix build .#homeConfigurations.electronics.activationPackage` | 2min | Syntax correct, attr exists, full profile builds with no collisions | nix installed, flake resolves |
| L2 | Dockerfile lint | `task image:build` | 30min | Package available in image at expected path | Assumes L1 work |

**Decision:** Start at L1. Gate catches syntax errors and typos in seconds. Execute catches collisions (like the `binutils`/`clang` collision). Only go to L2 for final validation before merge.

### Example 3: Entrypoint Script Change (docker domain)

**Task:** Fix ownership setting for `.local` and `.config` directories in entrypoint.

**Concern boundary analysis:**
```
Full pipeline: edit entrypoint.sh → docker image → container start → user created → dirs owned correctly
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                    Need container, but not full image rebuild
```

**Pyramid cascade:**

| Level | Gate | Execute | Cost | What it proves | What it assumes |
|-------|------|---------|------|----------------|-----------------|
| L1 | `bash -n entrypoint.sh` + shellcheck | Mount edited entrypoint into existing container, exec it | 30s | No syntax errors + ownership logic works correctly | Existing image has correct base, user creation works |
| L2 | Dockerfile lint | `task image:build` + fresh container | 30min | Full entrypoint flow from scratch | Everything |

**Decision:** Start at L1. Gate catches syntax errors in 2s. Execute validates ownership logic by bind-mounting into a running container. This avoids a 30-min rebuild for a 2-line fix.
