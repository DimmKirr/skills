export const meta = {
  name: 'git-group-commit',
  description: 'Group uncommitted changes by feature and generate a conventional commit message per group',
  whenToUse: 'Invoked by the git-group-commit skill to execute planning, message generation, and assembly with pinned models.',
  phases: [
    { title: 'Plan', detail: 'cluster the diff into groups, verify standalone builds, fetch tickets', model: 'sonnet' },
    { title: 'Messages', detail: 'one agent per group, scoped diff, format.md rules', model: 'sonnet' },
    { title: 'Assemble', detail: 'group-commit.sh --install: validate plan, stamp diffHash, install runner + alias', model: 'haiku' },
  ],
}

// Skill folder, needed for references/format.md and scripts/group-commit.sh.
// Optional arg; defaults to the standard Claude Code install location
// (`task link` symlinks every skill there). This workflow only runs on
// Claude Code, so that default is almost always right.
const skillDir = args?.skillDir ?? '~/.claude/skills/git-group-commit'
const dirNote = args?.skillDir
  ? ''
  : ` (if ${skillDir} is missing, locate the git-group-commit skill folder — e.g. skills/engineering/git-group-commit in this repo — and use it instead)`

const PLAN_SCHEMA = {
  type: 'object',
  required: ['groups', 'excluded', 'tickets'],
  properties: {
    groups: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'description', 'files'],
        properties: {
          name: { type: 'string' },
          description: { type: 'string' },
          notes: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    excluded: {
      type: 'array',
      items: {
        type: 'object',
        required: ['path', 'reason'],
        properties: { path: { type: 'string' }, reason: { type: 'string' } },
      },
    },
    tickets: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'title'],
        properties: { id: { type: 'string' }, title: { type: 'string' }, parent: { type: 'string' } },
      },
    },
  },
}

const MESSAGE_SCHEMA = {
  type: 'object',
  required: ['message'],
  properties: {
    message: {
      type: 'string',
      description:
        'Full commit message, real newlines. Line 1: plain-English header, NO type prefix. Line 2: blank. Then only "- type(scope): change — impact" bullets.',
    },
  },
}

// Deterministic format check — the structural rules of references/format.md that
// a skimming agent most often violates. Retry once with the violations named.
const BULLET_RE = /^- (feat|fix|refactor|test|docs|chore|perf|ci|build)\([^)]+\)!?: .+/
function validateMessage(msg) {
  const lines = msg.trim().split('\n')
  const errs = []
  if (/^[a-z]+(\([^)]*\))?!?:/.test(lines[0])) errs.push('header has a type prefix — the header must be plain English; types belong on bullets')
  if (lines.length < 3) errs.push('missing body — header, blank line, then typed bullets')
  else if (lines[1].trim() !== '') errs.push('line 2 must be blank')
  const bullets = lines.slice(2).filter((l) => l.trim())
  if (lines.length >= 3 && bullets.length === 0) errs.push('body must contain "- type(scope): ..." bullets')
  const bad = bullets.filter((l) => !BULLET_RE.test(l.trim()))
  if (bad.length) errs.push(`non-conforming bullet(s): ${bad.slice(0, 2).map((b) => JSON.stringify(b.trim())).join('; ')}`)
  if (bullets.length > 7) errs.push(`${bullets.length} bullets — cap is 7, group by purpose`)
  return errs
}

phase('Plan')
// stateKey: hash of the working-tree state, passed by the invoker. Baked into the
// prompt so a resume after ANY commit/edit re-plans instead of replaying a stale
// cached plan (agent results are cached by prompt+opts).
const stateKey = args?.stateKey ? `\n[working-tree state: ${args.stateKey}]` : ''
const plan = await agent(
  `You are the planning stage of the git-group-commit skill.${stateKey} Read ${skillDir}/SKILL.md${dirNote} steps 1-6 and execute them:
1. Gather state: git status, git diff HEAD, git log --oneline -20, git branch --show-current.
2. If $(git rev-parse --git-dir)/commits.json exists, prune groups whose files are all clean; keep its excluded list.
3. Cluster remaining uncommitted changes into independently-committable feature groups (one group is a normal outcome). Order by dependency. Exclude personal/local-environment paths into "excluded" with reasons. Every dirty path must land in exactly one group or in excluded — cross-check your file lists against git status before returning. A rename/move contributes TWO entries to its group: the old (deleted) path AND the new path; omitting the deletion leaves the old file in the commit.
4. If more than one group: verify each group's tree builds standalone. NEVER touch the real index (no git add / git reset on it — the user's staging must survive). Use a throwaway index inside ONE shell invocation (env does not persist between calls): export GIT_INDEX_FILE=$(mktemp -u); git read-tree HEAD; then per group, cumulatively: git add -- <group files>; S=$(mktemp -d); git archive "$(git write-tree)" | tar -x -C "$S"; run the project's build/validate command in "$S". Finally rm -f "$GIT_INDEX_FILE". Compare failures against plain HEAD before blaming a group. Move files between groups until each passes.
5. Extract ticket IDs from branch/commits/diff; fetch each from Linear/Jira MCP (use ToolSearch to load the tools) — return an empty tickets array if none.
Return the plan as structured output. Do NOT write commits.json and do NOT commit.`,
  { schema: PLAN_SCHEMA, model: 'sonnet', label: 'plan', phase: 'Plan' },
)
// A missing plan is an agent failure, not an empty tree — never report it as "nothing to do".
if (!plan) throw new Error('plan agent returned nothing — re-run to retry (cached stages replay)')
if (plan.groups.length === 0) return { committedPlan: false, reason: 'no uncommitted changes to group' }
log(`${plan.groups.length} group(s) planned, ${plan.excluded.length} path(s) excluded`)

phase('Messages')
const ticketCtx = plan.tickets.length
  ? `Tickets (reuse, do not refetch): ${JSON.stringify(plan.tickets)}`
  : 'No tickets found — omit the [ABC-xxx] header.'

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['ok', 'violations'],
  properties: {
    ok: { type: 'boolean' },
    violations: { type: 'array', items: { type: 'string' } },
  },
}

const msgPrompt = (g, ix) => `Write the commit message for ONE group of the git-group-commit plan.
Group ${ix + 1}: ${g.name} — ${g.description}
Files: ${JSON.stringify(g.files)}
${ticketCtx}
Diff ONLY this group: git diff HEAD -- <files> (use git diff --no-index /dev/null <file> for untracked). Never look at the full-tree diff.

MANDATORY structure (read ${skillDir}/references/format.md${dirNote} for the full rules and quality check):
[TICKET-IDs] <plain-English header — what changed for a user/API consumer; NO type prefix here>
<blank line>
- type(scope): what changed — consequence for the user/consumer
- type(scope): what changed — no user-facing impact
(types: feat|fix|refactor|test|docs|chore|perf|ci|build; scope mandatory; max 7 bullets; omit [TICKET-IDs] when this group has none)
NEVER add/insert Co-Authored-By or any other trailer line — the message ends with the last bullet. Each bullet is ONE short line (~15 words) — name the change, then the consequence; no run-on clauses. Cover every major NEW capability in the diff (new commands, scripts, integrations), not just moves/renames.`

const diffCmd = (g) =>
  `git diff HEAD -- ${g.files.map((f) => JSON.stringify(f)).join(' ')} (use git diff --no-index /dev/null <file> for untracked files)`

// Semantic review is evidence-based: the reviewer reads the group's diff itself.
// A reviewer that only sees the message can push toward plausible-sounding but
// unsupported claims (e.g. "no functional impact" on a lockfile bump).
const review = (g, message) =>
  agent(
    `Review this commit message for ONE group. First read the group's diff: ${diffCmd(g)}.
Flag, in priority order:
1. FACTUAL: any claim the diff does not support — wrong mechanism, conflated mechanisms (e.g. crediting one change with another's effect), invented or unverifiable impact (e.g. "no functional impact" on a dependency/lockfile bump the diff cannot prove harmless), changes attributed that are not in the diff.
2. MISSING: major new capabilities in the diff the message omits.
3. QUALITY per the "User-impact quality check" in ${skillDir}/references/format.md${dirNote}: header answers "what changed for the user", impact clauses state consequences not mechanisms, bullets under ~20 words, header not polluted by unrelated changes.
Every violation must quote the offending text and say what the diff actually shows. Do NOT check formatting. Do NOT demand an impact the diff cannot establish — for such changes the honest form names what changed (e.g. which inputs were bumped).
Message:
${message}
Group description: ${g.description}`,
    { schema: VERDICT_SCHEMA, model: 'sonnet', effort: 'low', label: `verify:${g.name}`, phase: 'Messages' },
  )

const MAX_ATTEMPTS = 3
// Structural check (regex) on every draft; semantic review on every draft that
// passes it (rewrites included — a rewrite can introduce new errors). Rewrites
// see the rejected draft and must change only what the violations name.
const genMessage = async (g, ix) => {
  const opts = (label) => ({
    schema: MESSAGE_SCHEMA,
    model: 'sonnet',
    ...(g.files.length > 10 ? {} : { effort: 'low' }),
    label,
    phase: 'Messages',
  })
  // Semantic review pays off when messages compete for scope (2+ groups) or the
  // group is large; a lone small group keeps just the structural check.
  const wantVerify = plan.groups.length > 1 || g.files.length > 10
  let prompt = msgPrompt(g, ix)
  let last = null
  let lastErrs = []
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const res = await agent(prompt, opts(attempt === 1 ? `msg:${g.name}` : `msg-retry${attempt - 1}:${g.name}`))
    let errs = res ? validateMessage(res.message) : ['agent returned nothing']
    const structuralOk = errs.length === 0
    if (structuralOk && wantVerify) {
      const verdict = await review(g, res.message)
      if (verdict && !verdict.ok) errs = verdict.violations
    }
    if (structuralOk) { last = res; lastErrs = errs }
    if (errs.length === 0) return res
    prompt = `${msgPrompt(g, ix)}

A previous draft was rejected.
Rejected draft:
${res ? res.message : '(none)'}
Violations: ${errs.join('; ')}
Fix ONLY what the violations name. Keep every statement they do not dispute. Re-read the diff before asserting any impact; never add a claim the diff does not show.`
  }
  if (!last) throw new Error(`group ${ix + 1} message still non-compliant after ${MAX_ATTEMPTS} attempts: ${lastErrs.join('; ')}`)
  // Structurally valid but review still objects: keep it, surface the objections
  // in the plan so `git group-commit --dry-run` shows them before anything commits.
  return { ...last, unresolved: lastErrs }
}
const messages = await parallel(plan.groups.map((g, ix) => () => genMessage(g, ix)))
if (messages.some((m) => !m)) throw new Error('a message agent failed — re-run to use cached results')

const commitsJson = {
  groups: plan.groups.map((g, ix) => ({
    name: g.name,
    description: g.description,
    ...(g.notes || messages[ix].unresolved
      ? { notes: [g.notes, messages[ix].unresolved && `REVIEW OBJECTIONS (unresolved, check the message): ${messages[ix].unresolved.join('; ')}`].filter(Boolean).join(' | ') }
      : {}),
    files: g.files,
    message: messages[ix].message,
  })),
  excluded: plan.excluded,
}

phase('Assemble')
// The agent only transports bytes: the plan goes through a QUOTED heredoc (no
// expansion) and group-commit.sh --install does every mechanical step itself —
// schema/path validation, diffHash stamping, runner copy, alias with literal
// quoting. The echoed canonical plan is then checked here, in code.
const INSTALL_SCHEMA = {
  type: 'object',
  required: ['exitCode', 'stdout'],
  properties: {
    exitCode: { type: 'number' },
    stdout: { type: 'string', description: 'complete stdout of the command, verbatim' },
    stderr: { type: 'string' },
  },
}
const planJson = JSON.stringify(commitsJson, null, 2)
const installPrompt = (feedback) => `Run the following as ONE shell invocation, copying it byte-for-byte. The heredoc delimiter is quoted, so nothing inside it is expanded — do not escape, reformat, or retype any part of it. Do not run anything else and do NOT commit.
${feedback ? `\nA previous attempt failed verification: ${feedback}\n` : ''}
PLAN=$(mktemp)
cat > "$PLAN" <<'GGC_PLAN_EOF'
${planJson}
GGC_PLAN_EOF
sh ${skillDir}/scripts/group-commit.sh --install "$PLAN"; echo "exit=$?"

Return the exit code and the complete stdout verbatim (and stderr if any).`

const norm = (x) => String(x ?? '').trim()
function verifyInstall(out) {
  if (!out) return 'agent returned nothing'
  if (out.exitCode !== 0) return `--install exited ${out.exitCode}: ${norm(out.stderr) || norm(out.stdout)}`
  const line = norm(out.stdout).split('\n').reverse().find((l) => l.trim().startsWith('{'))
  if (!line) return 'no canonical plan echoed on stdout'
  let got
  try { got = JSON.parse(line) } catch (e) { return `echoed plan is not JSON: ${e.message}` }
  if (!got.groups || got.groups.length !== commitsJson.groups.length) return 'group count differs from the plan'
  for (const [ix, want] of commitsJson.groups.entries()) {
    const have = got.groups[ix]
    if (norm(have.name) !== norm(want.name)) return `group ${ix + 1} name differs`
    if (JSON.stringify(have.files) !== JSON.stringify(want.files)) return `group ${ix + 1} files differ`
    if (norm(have.message) !== norm(want.message)) return `group ${ix + 1} message differs`
    if (!/^[0-9a-f]{40,64}$/.test(norm(have.diffHash))) return `group ${ix + 1} has no diffHash`
  }
  return null
}

let installErr = null
for (let attempt = 1; attempt <= 2; attempt++) {
  const out = await agent(installPrompt(installErr), {
    schema: INSTALL_SCHEMA, model: 'haiku', effort: 'low', label: attempt === 1 ? 'assemble' : 'assemble-retry', phase: 'Assemble',
  })
  installErr = verifyInstall(out)
  if (!installErr) break
}
if (installErr) {
  return { committedPlan: false, reason: `install failed verification: ${installErr} — inspect $(git rev-parse --git-dir)/commits.json before running git group-commit` }
}

return {
  committedPlan: true,
  groups: commitsJson.groups.map((g, ix) => ({
    n: ix + 1, name: g.name, files: g.files.length, header: g.message.split('\n')[0],
    ...(messages[ix].unresolved ? { reviewObjections: messages[ix].unresolved } : {}),
  })),
  excluded: plan.excluded,
  next: 'Review with `git group-commit --dry-run`, then run `git group-commit`.',
}
