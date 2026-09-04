#!/usr/bin/env bats
# State-matrix tests for group-commit.sh.
# Run: bats skills/engineering/git-group-commit/scripts/group-commit.test.bats
# Each test gets a throwaway git repo; the runner is exercised exactly as the
# `git group-commit` alias would run it.

# GC_SCRIPT override lets the suite run against another copy (e.g. the installed
# .git/group-commit.sh) — used to demonstrate RED on pre-feature versions.
SCRIPT="${GC_SCRIPT:-$BATS_TEST_DIRNAME/group-commit.sh}"

setup() {
  REPO="$BATS_TEST_TMPDIR/repo"
  mkdir -p "$REPO"
  cd "$REPO"
  git init -q
  git config user.email test@test
  git config user.name test
  echo base > base.txt
  git add . && git commit -qm base
  GD=$(git rev-parse --git-dir)
}

run_gc() { run sh "$SCRIPT" "$@"; }

plan() { printf '%s' "$1" > "$GD/commits.json"; }

two_dirty_groups() {
  echo a > a.txt
  echo b > b.txt
  plan '{"groups":[
    {"name":"A","files":["a.txt"],"message":"Add a\n\n- feat(a): add a — x"},
    {"name":"B","files":["b.txt"],"message":"Add b\n\n- feat(b): add b — x"}
  ],"excluded":[{"path":".env","reason":"secret"}]}'
}

# --- plan-file states -------------------------------------------------------

@test "missing commits.json fails with pointer to the skill" {
  run_gc
  [ "$status" -eq 1 ]
  [[ "$output" == *"run the git-group-commit skill first"* ]]
}

@test "empty plan exits 0 with friendly message and commits nothing" {
  plan '{"groups":[],"excluded":[]}'
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"plan is empty"* ]]
  [ "$(git rev-list --count HEAD)" -eq 1 ]
}

# --- commit states: present / missing / already committed -------------------

@test "all groups dirty: commits each, pops all, reports plan complete" {
  two_dirty_groups
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"2 committed — plan complete."* ]]
  [ "$(git rev-list --count HEAD)" -eq 3 ]
  [ "$(git log -1 --format=%s HEAD~1)" = "Add a" ]
  [ "$(git log -1 --format=%s HEAD)" = "Add b" ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 0 ]
  [ "$(jq '.excluded | length' "$GD/commits.json")" -eq 1 ]   # excluded survives the pop
}

@test "already-committed group: dropped from plan, no commit, honest summary" {
  echo a > a.txt && git add a.txt && git commit -qm "pre-existing a"
  echo b > b.txt
  plan '{"groups":[
    {"name":"A","files":["a.txt"],"message":"Add a"},
    {"name":"B","files":["b.txt"],"message":"Add b"}
  ],"excluded":[]}'
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"nothing to commit — already committed, dropping from plan"* ]]
  [[ "$output" == *"1 committed"* ]]
  [[ "$output" == *"1 dropped (already committed)"* ]]
  [ "$(git rev-list --count HEAD)" -eq 3 ]                     # base + pre-existing + B only
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 0 ]
}

@test "group file missing from disk entirely: dropped, not fatal" {
  echo b > b.txt
  plan '{"groups":[
    {"name":"ghost","files":["never-existed.txt"],"message":"Ghost"},
    {"name":"B","files":["b.txt"],"message":"Add b"}
  ],"excluded":[]}'
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"dropping from plan"* ]]
  [ "$(git log -1 --format=%s)" = "Add b" ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 0 ]
}

@test "untracked (new) files commit correctly" {
  echo new > brand-new.txt
  plan '{"groups":[{"name":"N","files":["brand-new.txt"],"message":"Add new file"}],"excluded":[]}'
  run_gc
  [ "$status" -eq 0 ]
  git ls-files --error-unmatch brand-new.txt
}

@test "rerun after full commit: plan empty, exit 0" {
  two_dirty_groups
  run_gc
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"plan is empty"* ]]
}

# --- skip-groups ------------------------------------------------------------

@test "skip-groups: skipped stays in commits.json, others commit and pop" {
  two_dirty_groups
  run_gc --skip-groups=1
  [ "$status" -eq 0 ]
  [[ "$output" == *"A — skipped, kept in commits.json"* ]]
  [[ "$output" == *"1 committed"* ]]
  [[ "$output" == *"1 skipped"* ]]
  [[ "$output" == *"remaining groups still in commits.json"* ]]
  [ "$(jq -r '.groups[0].name' "$GD/commits.json")" = "A" ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 1 ]
  [ "$(git log -1 --format=%s)" = "Add b" ]
}

@test "skip-groups then plain rerun commits the remainder" {
  two_dirty_groups
  run_gc --skip-groups=2
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 committed — plan complete."* ]]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 0 ]
}

@test "skip-groups rejects 0, out-of-range, and non-numeric" {
  two_dirty_groups
  run_gc --skip-groups=0;   [ "$status" -eq 2 ]
  run_gc --skip-groups=9;   [ "$status" -eq 2 ]
  run_gc --skip-groups=1,x; [ "$status" -eq 2 ]
  [ "$(git rev-list --count HEAD)" -eq 1 ]                     # nothing committed
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 2 ]      # nothing popped
}

# --- partial failure --------------------------------------------------------

@test "hook rejects group 2: group 1 stays committed and popped, group 2 survives" {
  two_dirty_groups
  mkdir -p "$GD/hooks"
  cat > "$GD/hooks/commit-msg" <<'EOF'
#!/bin/sh
if head -n1 "$1" | grep -q "Add b"; then echo "rejected by hook" >&2; exit 1; fi
exit 0
EOF
  chmod +x "$GD/hooks/commit-msg"
  run_gc
  [ "$status" -ne 0 ]
  [ "$(git log -1 --format=%s)" = "Add a" ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 1 ]      # only B remains
  [ "$(jq -r '.groups[0].name' "$GD/commits.json")" = "B" ]
}

# --- duplicate detection ----------------------------------------------------

@test "duplicate subject in history: blocked, kept in plan, exit 3" {
  echo a > a.txt && git add a.txt && git commit -qm "Add a"   # subject already in history
  echo a2 >> a.txt                                            # new content, same planned subject
  echo b > b.txt
  plan '{"groups":[
    {"name":"A","files":["a.txt"],"message":"Add a\n\n- feat(a): change a — x"},
    {"name":"B","files":["b.txt"],"message":"Add b\n\n- feat(b): add b — x"}
  ],"excluded":[]}'
  run_gc
  [ "$status" -eq 3 ]
  [[ "$output" == *"duplicate: subject already in recent history"* ]]
  [[ "$output" == *"1 blocked as duplicate"* ]]
  [ "$(git rev-list --count HEAD)" -eq 3 ]                    # base + Add a + Add b only
  [ "$(git log -1 --format=%s)" = "Add b" ]                   # B still committed
  [ "$(jq -r '.groups[0].name' "$GD/commits.json")" = "A" ]   # A kept for review
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 1 ]
}

@test "--force commits despite duplicate subject" {
  echo a > a.txt && git add a.txt && git commit -qm "Add a"
  echo a2 >> a.txt
  plan '{"groups":[{"name":"A","files":["a.txt"],"message":"Add a\n\n- feat(a): change a — x"}],"excluded":[]}'
  run_gc --force
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 committed — plan complete."* ]]
  [ "$(git rev-list --count HEAD)" -eq 3 ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 0 ]
}

@test "distinct subject with similar content is not a false positive" {
  echo a > a.txt && git add a.txt && git commit -qm "Add a"
  echo a2 >> a.txt
  plan '{"groups":[{"name":"A","files":["a.txt"],"message":"Extend a with a2\n\n- feat(a): extend a — x"}],"excluded":[]}'
  run_gc
  [ "$status" -eq 0 ]
  [ "$(git log -1 --format=%s)" = "Extend a with a2" ]
}

# --- staleness detection (diffHash) -----------------------------------------

@test "--hash prints a stable content hash that changes with content" {
  echo a > a.txt
  run sh "$SCRIPT" --hash a.txt
  [ "$status" -eq 0 ]
  H1=$output
  run sh "$SCRIPT" --hash a.txt
  [ "$output" = "$H1" ]                                        # deterministic
  echo more >> a.txt
  run sh "$SCRIPT" --hash a.txt
  [ "$output" != "$H1" ]                                       # content-sensitive
}

@test "stale group (content changed since planning): blocked, kept, exit 3" {
  echo a > a.txt
  echo b > b.txt
  HA=$(sh "$SCRIPT" --hash a.txt)
  plan "{\"groups\":[
    {\"name\":\"A\",\"files\":[\"a.txt\"],\"diffHash\":\"$HA\",\"message\":\"Add a\n\n- feat(a): add a — x\"},
    {\"name\":\"B\",\"files\":[\"b.txt\"],\"message\":\"Add b\n\n- feat(b): add b — x\"}
  ],\"excluded\":[]}"
  echo tampered >> a.txt                                       # content drifts after review
  run_gc
  [ "$status" -eq 3 ]
  [[ "$output" == *"stale: content changed since planning"* ]]
  [[ "$output" == *"1 blocked as stale"* ]]
  [ "$(git log -1 --format=%s)" = "Add b" ]                    # B (no hash) still commits
  [ "$(git rev-list --count HEAD)" -eq 2 ]
  [ "$(jq -r '.groups[0].name' "$GD/commits.json")" = "A" ]    # A kept for re-planning
}

@test "matching diffHash commits normally" {
  echo a > a.txt
  HA=$(sh "$SCRIPT" --hash a.txt)
  plan "{\"groups\":[{\"name\":\"A\",\"files\":[\"a.txt\"],\"diffHash\":\"$HA\",\"message\":\"Add a\n\n- feat(a): add a — x\"}],\"excluded\":[]}"
  run_gc
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 committed — plan complete."* ]]
}

@test "--force commits despite stale diffHash" {
  echo a > a.txt
  HA=$(sh "$SCRIPT" --hash a.txt)
  plan "{\"groups\":[{\"name\":\"A\",\"files\":[\"a.txt\"],\"diffHash\":\"$HA\",\"message\":\"Add a\n\n- feat(a): add a — x\"}],\"excluded\":[]}"
  echo tampered >> a.txt
  run_gc --force
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 committed — plan complete."* ]]
}

# --- dry-run ----------------------------------------------------------------

@test "dry-run prints plan, commits nothing, pops nothing" {
  two_dirty_groups
  run_gc --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== Group 1/2: A ==="* ]]
  [[ "$output" == *"=== Excluded (not in any group) ==="* ]]
  [ "$(git rev-list --count HEAD)" -eq 1 ]
  [ "$(jq '.groups | length' "$GD/commits.json")" -eq 2 ]
}

@test "dry-run with skip-groups tags the group SKIPPED" {
  two_dirty_groups
  run_gc -n --skip-groups=2
  [ "$status" -eq 0 ]
  [[ "$output" == *"B ==="*"[SKIPPED]"* ]]
}

# --- flags & output ---------------------------------------------------------

@test "help exits 0; unknown flag exits 2 with usage" {
  run_gc --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"usage: git group-commit"* ]]
  run_gc --bogus
  [ "$status" -eq 2 ]
  [[ "$output" == *"usage: git group-commit"* ]]
}

@test "no ANSI escapes when piped (non-TTY) and under NO_COLOR" {
  two_dirty_groups
  run_gc --dry-run
  [[ "$output" != *$'\033'* ]]
  NO_COLOR=1 run_gc --dry-run
  [[ "$output" != *$'\033'* ]]
}
