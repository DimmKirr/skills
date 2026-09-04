#!/bin/sh
# Generate ONE group's commit message on a pinned (cheap) Codex model,
# regardless of what model the calling session runs.
# Usage: codex-msg.sh <skill-dir> <out-file> <file>...
# Overrides: GROUP_COMMIT_MSG_MODEL (default gpt-5.1-codex-mini), CODEX_BIN (default codex)
set -eu
[ $# -ge 3 ] || { echo "usage: codex-msg.sh <skill-dir> <out-file> <file>..." >&2; exit 2; }
SKILL_DIR=$1
OUT=$2
shift 2
MODEL=${GROUP_COMMIT_MSG_MODEL:-gpt-5.1-codex-mini}
CODEX=${CODEX_BIN:-codex}

DIFF=$(mktemp)
trap 'rm -f "$DIFF"' EXIT
for f in "$@"; do
  if git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
    git diff HEAD -- "$f"
  else
    git diff --no-index -- /dev/null "$f" || true   # exits 1 on diff by design
  fi
done > "$DIFF"
[ -s "$DIFF" ] || { echo "no diff for given files" >&2; exit 1; }

{
  echo "Write a git commit message for exactly the diff below — nothing outside it."
  echo "Follow the format rules in $SKILL_DIR/references/format.md exactly (header, typed bullets with scopes and impact clauses, user-impact quality check)."
  echo "Output ONLY the commit message text, no fences, no commentary."
  echo
  cat "$DIFF"
} | "$CODEX" exec -m "$MODEL" -s read-only --ephemeral --skip-git-repo-check -o "$OUT" - >/dev/null

[ -s "$OUT" ] || { echo "codex exec produced no message" >&2; exit 1; }
