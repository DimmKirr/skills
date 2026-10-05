---
name: continue-debug
description: Analyze the output of the most recent debug run in .scratch/debug/ and iterate with ranked hypotheses.
disable-model-invocation: true
---

# Debug Continue

The user has run a debug command (e.g., `task debug:colima`) and wants you to analyze the output and iterate on the debugging process.

## Context (auto-injected on supported platforms)

!ls -la .scratch/debug/

## Instructions

1. **Read debug output**: Read all files in `.scratch/debug/` in the project root (listing auto-injected above if available). These contain the output from the most recent debug run.

2. **Analyze locally**: Study the debug output carefully. Cross-reference with the project's nix configuration, any relevant upstream documentation, and your knowledge of the system.

3. **Research online**: Search the web for the key symptoms, error messages, and version-specific behaviors found in the debug output. Look for:
   - GitHub issues, bug trackers, and mailing list threads matching the symptoms
   - Forum posts (Proxmox, Arch, NixOS, etc.) describing similar failures with the same hardware/software versions
   - Upstream changelogs or release notes that mention fixes for the observed behavior
   - Known bugs, CVEs, or regressions tied to the specific kernel, firmware, or driver versions in play
   - Use WebSearch or the playwright MCP tool. Extract specific corroborating or contradicting evidence.

4. **Hypotheses**: Identify the **top 3 most probable hypotheses** for the root cause of the issue. For each hypothesis:
   - State the hypothesis clearly in one sentence
   - Cite the specific evidence from the debug output that supports it
   - Cite any corroborating or contradicting evidence found online (with source links)
   - State what evidence would confirm or refute it
   - Rate confidence: low / medium / high

5. **Enhance debug command**: Update the Taskfile debug task that generated this output to collect **more granular data** that would prove or disprove your hypotheses. Add:
   - More verbose/trace-level logging flags where available
   - Additional stdout/stderr capture from relevant subsystems
   - Counters, timestamps, and state dumps
   - Kernel/system debug info relevant to the hypotheses
   - Any commands that would directly confirm or rule out each hypothesis
   - Checks suggested by online findings (e.g., if a forum post says "check X register", add that check)
   - Comments in the debug task explaining which hypothesis each new check targets

6. **Report**: Summarize your findings and tell the user to re-run the debug command. Include:
   - What the online research revealed (key links and takeaways)
   - What new data you added to the debug task and which hypothesis each targets
   - Which hypotheses were strengthened or weakened by online evidence

## Goal

Each iteration of this loop should narrow the problem space. After 2-3 cycles of run -> analyze -> research -> enhance, the root cause should be identified with high confidence. Online research is critical for avoiding dead ends: if 50 people hit the same bug and the fix is a kernel parameter, that saves cycles vs. blind instrumentation.

## Examples

**Iteration 1:** User runs `task debug:colima`, output shows `FATA[0005] error starting VM: timeout`. Reads debug output, then searches web for "colima FATA error starting VM timeout". Finds GitHub issue #847 reporting same error with VZ driver on macOS 14.2. Ranks hypotheses: (1) VZ driver regression in macOS 14.2 (evidence: debug shows macOS 14.2, GitHub issue matches exactly, confidence: high), (2) stale VM state from unclean shutdown (evidence: previous crash in logs, confidence: medium), (3) CPU/memory limits too low (evidence: VM config shows 2GB, but no OOM in logs, confidence: low). Enhances debug task with VZ-specific checks from the GitHub issue.

**Iteration 2:** Re-run confirms VZ driver hypothesis. Online research found the fix: `colima start --vm-type qemu` as workaround, or upgrade to macOS 14.3 where Apple patched the regression. Root cause confirmed with high confidence in 2 cycles.
