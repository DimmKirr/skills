#!/bin/sh
# Runner for the git-group-commit skill. Reads commits.json from the git dir.
set -eu

case $0 in /*) SELF=$0 ;; *) SELF=$PWD/$0 ;; esac
ORIG_PWD=$PWD
# Plan paths are repo-relative: always work from the repo root. (Git shell
# aliases already run there; direct `sh path/to/group-commit.sh` calls may not.)
cd "$(git rev-parse --show-toplevel)"
GIT_DIR=$(git rev-parse --git-dir)
# Single-quoted on purpose: $(...) must stay literal in the alias so it resolves
# the git dir at run time, from any subdirectory or worktree.
ALIAS='!sh "$(git rev-parse --git-dir)/group-commit.sh"'
EMPTY_HASH=$(printf '' | git hash-object --stdin)

usage() {
  cat <<'USAGE'
usage: git group-commit [--dry-run] [--skip-groups=N,N,...] [--force] [--no-color] [--help]
       git group-commit --hash <file>...        print the staleness fingerprint for a file set
       group-commit.sh --install [plan.json]    install runner + alias; with a plan, validate
                                                it, stamp diffHashes, write commits.json

Commit the groups planned in <git-dir>/commits.json, in order.

  (no flag)             commit each group in sequence
  --dry-run, -n         print the full plan (groups, files, messages, exclusions)
                        without committing (--review is accepted as an alias)
  --skip-groups=1,3     skip these groups (1-based numbers as shown in the plan);
                        they stay in commits.json for a later run
  --force               commit even when a group is blocked as a duplicate (subject
                        already in recent history) or stale (content changed since
                        the plan's diffHash was recorded), or when planned files are
                        partially staged (the whole file gets committed)
  --no-color            disable ANSI colors (also honored: NO_COLOR env, non-TTY output)
  --help, -h            show this help

All paths are repo-relative. The plan is written by the git-group-commit skill;
edit commits.json to adjust it.
USAGE
}

# One path's uncommitted diff: tracked → vs HEAD; untracked on disk → vs /dev/null;
# gone from both disk and index (a deletion already committed) → nothing.
diff_one() {
  if git ls-files --error-unmatch -- ":(literal)$1" >/dev/null 2>&1; then
    git diff HEAD -- ":(literal)$1"
  elif [ -e "$1" ] || [ -L "$1" ]; then
    git diff --no-index -- /dev/null "$1" || true   # exits 1 on diff by design
  fi
}

# Staleness fingerprint of a file set (one path per line on stdin). A set whose
# changes are all committed hashes to EMPTY_HASH.
hash_list() {
  while IFS= read -r f; do
    if [ -n "$f" ]; then diff_one "$f"; fi
  done | git hash-object --stdin
}

# A path a plan may legitimately name: on disk, in the index, or in history
# (a deletion since committed). Anything else is a typo in the plan.
path_known() {
  [ -e "$1" ] || [ -L "$1" ] ||
    git ls-files --error-unmatch -- ":(literal)$1" >/dev/null 2>&1 ||
    [ -n "$(git log -1 --format=%H -- ":(literal)$1" 2>/dev/null)" ]
}

unknown_paths() {   # stdin: paths; stdout: the ones path_known rejects
  while IFS= read -r f; do
    if [ -n "$f" ] && ! path_known "$f"; then printf '%s\n' "$f"; fi
  done
}

# Planned files with BOTH staged and unstaged changes (a `git add -p` split).
# The runner stages whole files, so committing would silently fold the
# unstaged hunks in. stdin: planned paths.
partially_staged() {
  both=$( { git diff --cached --name-only; git diff --name-only; } | sort | uniq -d )
  while IFS= read -r f; do
    if [ -n "$both" ] && printf '%s\n' "$both" | grep -Fxq -- "$f"; then printf '%s\n' "$f"; fi
  done
}

indent() { sed 's/^/  /'; }

# --- subcommands ------------------------------------------------------------

if [ "${1:-}" = "--hash" ]; then
  shift
  [ $# -ge 1 ] || { echo "usage: git group-commit --hash <file>..." >&2; exit 2; }
  for f in "$@"; do printf '%s\n' "$f"; done | hash_list
  exit 0
fi

if [ "${1:-}" = "--install" ]; then
  shift
  [ $# -le 1 ] || { echo "usage: group-commit.sh --install [plan.json]" >&2; exit 2; }
  DEST="$GIT_DIR/group-commit.sh"
  [ "$SELF" -ef "$DEST" ] || cp "$SELF" "$DEST"
  chmod +x "$DEST"
  git config alias.group-commit "$ALIAS"
  [ "$(git config --get alias.group-commit)" = "$ALIAS" ] ||
    { echo "install: alias.group-commit readback does not match" >&2; exit 1; }
  echo "installed: $DEST, alias.group-commit"
  [ $# -eq 1 ] || exit 0

  PLAN=$1
  case $PLAN in /*) ;; *) PLAN=$ORIG_PWD/$PLAN ;; esac
  [ -f "$PLAN" ] || { echo "install: no plan file $PLAN" >&2; exit 2; }
  jq -e '
    (.groups | type == "array" and length > 0)
    and all(.groups[];
      (.name | type == "string" and length > 0)
      and (.message | type == "string" and length > 0)
      and (.files | type == "array" and length > 0 and all(.[]; type == "string" and length > 0)))
    and ((.excluded // []) | type == "array")' "$PLAN" >/dev/null 2>&1 ||
    { echo "install: plan fails schema — need non-empty groups[] each with name, message, non-empty files[]; optional excluded[]" >&2; exit 2; }
  DUPS=$(jq -r '[.groups[].files[]] | group_by(.) | map(select(length > 1) | .[0]) | .[]' "$PLAN")
  [ -z "$DUPS" ] || { echo "install: path(s) planned in more than one group:" >&2; printf '%s\n' "$DUPS" | indent >&2; exit 2; }
  BAD=$(jq -r '.groups[].files[]' "$PLAN" | unknown_paths)
  [ -z "$BAD" ] || { echo "install: unknown path(s) — not on disk, in the index, or in history:" >&2; printf '%s\n' "$BAD" | indent >&2; exit 2; }

  N=$(jq '.groups | length' "$PLAN")
  HASHES=$(i=0; while [ "$i" -lt "$N" ]; do
    jq -r ".groups[$i].files[]" "$PLAN" | hash_list; i=$((i+1))
  done | jq -R . | jq -s -c .)
  TMP="$GIT_DIR/commits.json.tmp"
  jq --argjson h "$HASHES" \
    '.groups |= [to_entries[] | .value + {diffHash: $h[.key]}] | .excluded = (.excluded // [])' \
    "$PLAN" > "$TMP"
  mv "$TMP" "$GIT_DIR/commits.json"
  # Echo the canonical plan back so callers can verify what actually landed.
  jq -c '{groups: [.groups[] | {name, files, message, diffHash}], excluded}' "$GIT_DIR/commits.json"
  exit 0
fi

# --- runner -----------------------------------------------------------------

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

JSON="$GIT_DIR/commits.json"
[ -f "$JSON" ] || { echo "no $JSON — run the git-group-commit skill first" >&2; exit 1; }
COUNT=$(jq '.groups | length' "$JSON")
[ "$COUNT" -gt 0 ] || { echo "plan is empty — nothing to commit (re-invoke the git-group-commit skill to plan)"; exit 0; }

if [ -n "$SKIP" ]; then
  for n in $(printf '%s' "$SKIP" | tr ',' ' '); do
    [ "$n" -ge 1 ] && [ "$n" -le "$COUNT" ] || { echo "--skip-groups: no group $n (plan has $COUNT)" >&2; exit 2; }
  done
fi

PARTIAL=$(jq -r '.groups[].files[]' "$JSON" | partially_staged)

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
  BAD=$(jq -r '.groups[].files[]' "$JSON" | unknown_paths)
  if [ -n "$BAD" ]; then
    printf '\n%s\n' "${RED}warning: unknown path(s) — their groups will be blocked:${R}"
    printf '%s\n' "$BAD" | indent
  fi
  if [ -n "$PARTIAL" ]; then
    printf '\n%s\n' "${RED}warning: partially staged — a real run refuses without --force:${R}"
    printf '%s\n' "$PARTIAL" | indent
  fi
  exit 0
fi

if [ -n "$PARTIAL" ] && [ "$FORCE" -ne 1 ]; then
  {
    echo "partially staged planned file(s) — group-commit stages whole files, so the unstaged hunks would be committed too:"
    printf '%s\n' "$PARTIAL" | indent
    echo "commit or stash the split first, or rerun with --force to commit whole files"
  } >&2
  exit 2
fi

DONE=0
DROPPED=0
SKIPPED_N=0
BLOCKED=0
STALE=0
UNKNOWN=0
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
  FILES=$(jq -r ".groups[$i].files[]" "$JSON")
  # unknown-path guard: a path that is nowhere (disk, index, history) is a typo
  # in the plan — committing without it would silently lose part of the group
  BAD=$(printf '%s\n' "$FILES" | unknown_paths)
  if [ -n "$BAD" ]; then
    printf '%s\n' "${RED}unknown path(s) — not on disk, in the index, or in history; kept in commits.json (fix the path):${R}"
    printf '%s\n\n' "$BAD" | indent
    UNKNOWN=$((UNKNOWN+1))
    i=$N
    continue
  fi
  # already-committed check comes BEFORE staleness: a group committed by other
  # means has an empty diff, which is "done", not "content changed"
  HAVE=$(printf '%s\n' "$FILES" | hash_list)
  if [ "$HAVE" = "$EMPTY_HASH" ]; then
    printf '%s\n\n' "${YELLOW}nothing to commit — already committed, dropping from plan${R}"
    DROPPED=$((DROPPED+1))
    DONE_IDX="$DONE_IDX,$i"
    i=$N
    continue
  fi
  # staleness guard: the plan recorded a fingerprint of this group's diff at
  # planning time — if the content changed since review, block unless --force
  WANT=$(jq -r ".groups[$i].diffHash // empty" "$JSON")
  if [ -n "$WANT" ] && [ "$FORCE" -ne 1 ] && [ "$HAVE" != "$WANT" ]; then
    printf '%s\n\n' "${RED}stale: content changed since planning — kept in commits.json (re-invoke the git-group-commit skill, or rerun with --force)${R}"
    STALE=$((STALE+1))
    i=$N
    continue
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
  git reset -q HEAD -- . 2>/dev/null || true
  # stage each file; a path gone from disk AND index is a deletion that is
  # already committed — nothing to stage. Any other `git add` failure aborts.
  printf '%s\n' "$FILES" | while IFS= read -r f; do
    if git ls-files --error-unmatch -- ":(literal)$f" >/dev/null 2>&1 || [ -e "$f" ] || [ -L "$f" ]; then
      git add -- ":(literal)$f"
    fi
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
[ "$UNKNOWN" -gt 0 ] && SUMMARY="$SUMMARY${RED}, $UNKNOWN blocked by unknown paths${R}"
[ "$SKIPPED_N" -gt 0 ] && SUMMARY="$SUMMARY${YELLOW}, $SKIPPED_N skipped${R}"
if [ "$SKIPPED_N" -gt 0 ] || [ "$BLOCKED" -gt 0 ] || [ "$STALE" -gt 0 ] || [ "$UNKNOWN" -gt 0 ]; then
  SUMMARY="$SUMMARY${YELLOW} — remaining groups still in commits.json${R}"
else
  SUMMARY="$SUMMARY — plan complete."
fi
printf '%s\n' "$SUMMARY"
[ "$((BLOCKED + STALE + UNKNOWN))" -eq 0 ] || exit 3
