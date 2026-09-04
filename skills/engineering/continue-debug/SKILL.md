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

2. **Analyze**: Study the debug output carefully. Cross-reference with the project's nix configuration, any relevant upstream documentation, and your knowledge of the system.

3. **Hypotheses**: Identify the **top 3 most probable hypotheses** for the root cause of the issue. For each hypothesis:
   - State the hypothesis clearly in one sentence
   - Cite the specific evidence from the debug output that supports it
   - State what evidence would confirm or refute it

4. **Enhance debug command**: Update the Taskfile debug task that generated this output to collect **more granular data** that would prove or disprove your hypotheses. Add:
   - More verbose/trace-level logging flags where available
   - Additional stdout/stderr capture from relevant subsystems
   - Counters, timestamps, and state dumps
   - Kernel/system debug info relevant to the hypotheses
   - Any commands that would directly confirm or rule out each hypothesis
   - Comments in the debug task explaining which hypothesis each new check targets

5. **Report**: Summarize your findings and tell the user to re-run the debug command. Explain what new data you added and which hypothesis each new check targets.

## Goal

Each iteration of this loop should narrow the problem space. After 2-3 cycles of run -> analyze -> enhance, the root cause should be identified with high confidence.

## Examples

**Iteration 1:** User runs `task debug:colima`, output shows `FATA[0005] error starting VM: timeout`. Skill reads `.scratch/debug/`, ranks hypotheses: (1) CPU/memory limits too low (evidence: VM config shows 2GB), (2) network timeout during image pull (evidence: no DNS resolution logged), (3) stale VM state (evidence: previous unclean shutdown). Enhances debug task with `--verbose`, memory stats, DNS probe.

**Iteration 2:** Re-run with enhanced logging shows DNS resolving but TCP connection refused on port 2376. Hypothesis #2 eliminated. New top hypothesis: Docker socket not bound. Adds `ss -tlnp` and `docker context inspect` to debug task. Root cause identified next cycle: Docker context pointing to wrong endpoint after OS update.
