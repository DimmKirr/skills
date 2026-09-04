#!/bin/sh
# Runner for the git-group-commit skill. Reads commits.json from the git dir.
set -eu

# Content hash of a file set's uncommitted diff — the staleness fingerprint.
# Planners store it as groups[].diffHash; the runner recomputes before committing.
hash_files() {
  for f in "$@"; do
    if git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
      git diff HEAD -- "$f"
    else
      git diff --no-index -- /dev/null "$f" || true   # exits 1 on diff by design
    fi
  done | git hash-object --stdin
}

if [ "${1:-}" = "--hash" ]; then
  shift
  [ $# -ge 1 ] || { echo "usage: git group-commit --hash <file>..." >&2; exit 2; }
  hash_files "$@"
  exit 0
fi

usage() {
  cat <<'USAGE'
usage: git group-commit [--dry-run] [--skip-groups=N,N,...] [--force] [--no-color] [--help]
       git group-commit --hash <file>...   print the staleness fingerprint for a file set

Commit the groups planned in <git-dir>/commits.json, in order.

  (no flag)             commit each group in sequence
  --dry-run, -n         print the full plan (groups, files, messages, exclusions)
                        without committing (--review is accepted as an alias)
  --skip-groups=1,3     skip these groups (1-based numbers as shown in the plan);
                        they stay in commits.json for a later run
  --force               commit even when a group is blocked as a duplicate (subject
                        already in recent history) or stale (content changed since
                        the plan's diffHash was recorded)
  --no-color            disable ANSI colors (also honored: NO_COLOR env, non-TTY output)
  --help, -h            show this help

The plan is written by the git-group-commit skill; edit commits.json to adjust it.
USAGE
}

DRY=0
COLOR=auto
SKIP=''
FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --dry-run|-n|--review) DRY=1 ;;
    --no-color) COLOR=never ;;
    --force) FORCE=1 ;;
    --skip-groups=*)
      SKIP=${1#--skip-groups=}
      case ",$SKIP," in
        *[!0-9,]*|,,*|*,,) echo "invalid --skip-groups value: '$SKIP' (expected e.g. 1,3)" >&2; exit 2 ;;
      esac ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

skipped() { case ",$SKIP," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

if [ "$COLOR" = auto ] && [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then COLOR=always; fi
if [ "$COLOR" = always ]; then
  B=$(printf '\033[1m'); DIM=$(printf '\033[2m'); CYAN=$(printf '\033[36m')
  GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m'); RED=$(printf '\033[31m')
  R=$(printf '\033[0m')
else
  B=''; DIM=''; CYAN=''; GREEN=''; YELLOW=''; RED=''; R=''
fi

GIT_DIR=$(git rev-parse --git-dir)
JSON="$GIT_DIR/commits.json"
[ -f "$JSON" ] || { echo "no $JSON — run the git-group-commit skill first" >&2; exit 1; }
COUNT=$(jq '.groups | length' "$JSON")
[ "$COUNT" -gt 0 ] || { echo "plan is empty — nothing to commit (re-invoke the git-group-commit skill to plan)"; exit 0; }

if [ -n "$SKIP" ]; then
  for n in $(printf '%s' "$SKIP" | tr ',' ' '); do
    [ "$n" -ge 1 ] && [ "$n" -le "$COUNT" ] || { echo "--skip-groups: no group $n (plan has $COUNT)" >&2; exit 2; }
  done
fi

if [ "$DRY" = 1 ]; then
  jq -r --arg b "$B" --arg dim "$DIM" --arg cyan "$CYAN" --arg green "$GREEN" \
        --arg yellow "$YELLOW" --arg red "$RED" --arg r "$R" --arg skip ",$SKIP," '
    (.groups | length) as $n
    | (.groups | to_entries[]
       | ",\(.key + 1)," as $me
       | (if $skip | contains($me) then " \($yellow)[SKIPPED]\($r)" else "" end) as $tag
       | "\($b)\($cyan)=== Group \(.key + 1)/\($n): \(.value.name) ===\($r)\($tag)",
         "  \(.value.description // "")",
         (if .value.notes then "  \($yellow)note: \(.value.notes)\($r)" else empty end),
         "",
         "  \($dim)files (\(.value.files | length)):\($r)",
         (.value.files[] | "    \(.)"),
         "",
         "  \($dim)message:\($r)",
         (.value.message | split("\n")[] | "    \($green)\(.)\($r)"),
         ""),
      (if (.excluded // []) | length > 0 then
         "\($b)\($red)=== Excluded (not in any group) ===\($r)",
         (.excluded[] | "  \($yellow)\(.path)\($r) — \(.reason)")
       else empty end)
  ' "$JSON"
  exit 0
fi

DONE=0
DROPPED=0
SKIPPED_N=0
BLOCKED=0
STALE=0
DONE_IDX=''   # 0-based indices committed (or found already clean) — popped from commits.json at the end
pop_done() {
  [ -n "$DONE_IDX" ] || return 0
  TMP=$(mktemp)
  jq --arg drop "${DONE_IDX#,}" \
    '($drop | split(",") | map(tonumber)) as $d
     | .groups |= (to_entries | map(select(.key as $k | ($d | index($k)) | not)) | map(.value))' \
    "$JSON" > "$TMP" && mv "$TMP" "$JSON"
}
trap pop_done EXIT

i=0
while [ "$i" -lt "$COUNT" ]; do
  N=$((i+1))
  NAME=$(jq -r ".groups[$i].name" "$JSON")
  if skipped "$N"; then
    printf '%s\n\n' "${YELLOW}=== Group $N/$COUNT: $NAME — skipped, kept in commits.json ===${R}"
    SKIPPED_N=$((SKIPPED_N+1))
    i=$N
    continue
  fi
  printf '%s\n' "${B}${CYAN}=== Group $N/$COUNT: $NAME ===${R}"
  # staleness guard: the plan recorded a fingerprint of this group's diff at
  # planning time — if the content changed since review, block unless --force
  WANT=$(jq -r ".groups[$i].diffHash // empty" "$JSON")
  if [ -n "$WANT" ] && [ "$FORCE" -ne 1 ]; then
    HAVE=$(jq -r ".groups[$i].files[]" "$JSON" | tr '\n' '\0' | xargs -0 sh "$0" --hash)
    if [ "$HAVE" != "$WANT" ]; then
      printf '%s\n\n' "${RED}stale: content changed since planning — kept in commits.json (re-invoke the git-group-commit skill, or rerun with --force)${R}"
      STALE=$((STALE+1))
      i=$N
      continue
    fi
  fi
  # duplicate guard: an identical subject in recent history usually means a stale
  # plan is re-committing work under an old message — block unless --force
  SUBJ=$(jq -r ".groups[$i].message" "$JSON" | head -n1)
  if [ "$FORCE" -ne 1 ] && git log --format=%s -100 2>/dev/null | grep -Fxq "$SUBJ"; then
    printf '%s\n\n' "${RED}duplicate: subject already in recent history — kept in commits.json (edit the message or rerun with --force)${R}"
    BLOCKED=$((BLOCKED+1))
    i=$N
    continue
  fi
  # reset index so only this group's files are staged
  git reset HEAD -- . >/dev/null 2>&1 || true
  jq -r ".groups[$i].files[]" "$JSON" | while IFS= read -r f; do
    git add -- ":/$f" 2>/dev/null || true   # tolerate files already committed/deleted
  done
  if git diff --cached --quiet; then
    printf '%s\n\n' "${YELLOW}nothing to commit — already committed, dropping from plan${R}"
    DROPPED=$((DROPPED+1))
    DONE_IDX="$DONE_IDX,$i"
    i=$N
    continue
  fi
  jq -r ".groups[$i].message" "$JSON" | git commit -F -
  echo
  DONE=$((DONE+1))
  DONE_IDX="$DONE_IDX,$i"
  i=$N
done

SUMMARY="${B}${GREEN}$DONE committed${R}"
[ "$DROPPED" -gt 0 ] && SUMMARY="$SUMMARY${YELLOW}, $DROPPED dropped (already committed)${R}"
[ "$BLOCKED" -gt 0 ] && SUMMARY="$SUMMARY${RED}, $BLOCKED blocked as duplicate${R}"
[ "$STALE" -gt 0 ] && SUMMARY="$SUMMARY${RED}, $STALE blocked as stale${R}"
[ "$SKIPPED_N" -gt 0 ] && SUMMARY="$SUMMARY${YELLOW}, $SKIPPED_N skipped${R}"
if [ "$SKIPPED_N" -gt 0 ] || [ "$BLOCKED" -gt 0 ] || [ "$STALE" -gt 0 ]; then
  SUMMARY="$SUMMARY${YELLOW} — remaining groups still in commits.json${R}"
else
  SUMMARY="$SUMMARY — plan complete."
fi
printf '%s\n' "$SUMMARY"
[ "$((BLOCKED + STALE))" -eq 0 ] || exit 3
