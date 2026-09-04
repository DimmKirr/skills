export const meta = {
  name: 'git-group-commit',
  description: 'Group uncommitted changes by feature and generate a conventional commit message per group',
  whenToUse: 'Invoked by the git-group-commit skill to execute planning, message generation, and assembly with pinned models.',
  phases: [
    { title: 'Plan', detail: 'cluster the diff into groups, verify standalone builds, fetch tickets', model: 'sonnet' },
    { title: 'Messages', detail: 'one agent per group, scoped diff, format.md rules', model: 'sonnet' },
    { title: 'Assemble', detail: 'write commits.json, install runner + alias', model: 'haiku' },
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
4. If more than one group: verify each group's staged tree builds standalone (cumulative git add, git write-tree + git archive to a temp dir, project's build/validate command; reset index afterwards). Move files between groups until each passes.
5. Extract ticket IDs from branch/commits/diff; fetch each from Linear/Jira MCP (use ToolSearch to load the tools) — return an empty tickets array if none.
Return the plan as structured output. Do NOT write commits.json and do NOT commit.`,
  { schema: PLAN_SCHEMA, model: 'sonnet', label: 'plan', phase: 'Plan' },
)
if (!plan || plan.groups.length === 0) return { committedPlan: false, reason: 'no uncommitted changes to group' }
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

// Structural retry (regex-checked), then semantic verify against format.md's
// user-impact quality rules, with one corrective retry on violations.
const genMessage = async (g, ix) => {
  const opts = (label) => ({
    schema: MESSAGE_SCHEMA,
    model: 'sonnet',
    ...(g.files.length > 10 ? {} : { effort: 'low' }),
    label,
    phase: 'Messages',
  })
  let res = await agent(msgPrompt(g, ix), opts(`msg:${g.name}`))
  let errs = res ? validateMessage(res.message) : ['agent returned nothing']
  if (errs.length === 0) {
    const verdict = await agent(
      `Strictly review this commit message against the "User-impact quality check" in ${skillDir}/references/format.md${dirNote}: header answers "what changed for the user", impact clauses state consequences (not mechanisms, not restatements), internal bullets stay brief, header not polluted by unrelated changes. Also flag: bullets over ~20 words, and major new capabilities in the file list that the message omits. Do NOT check formatting — only content quality.
Message:
${res.message}
Group description: ${g.description}`,
      { schema: VERDICT_SCHEMA, model: 'sonnet', effort: 'low', label: `verify:${g.name}`, phase: 'Messages' },
    )
    if (verdict && !verdict.ok) errs = verdict.violations
  }
  if (errs.length) {
    res = await agent(
      `${msgPrompt(g, ix)}

A previous attempt was rejected for: ${errs.join('; ')}. Produce a fully compliant message.`,
      opts(`msg-retry:${g.name}`),
    )
    const finalErrs = res ? validateMessage(res.message) : ['agent returned nothing']
    if (finalErrs.length) throw new Error(`group ${ix + 1} message still non-compliant: ${finalErrs.join('; ')}`)
  }
  return res
}
const messages = await parallel(plan.groups.map((g, ix) => () => genMessage(g, ix)))
if (messages.some((m) => !m)) throw new Error('a message agent failed — re-run to use cached results')

const commitsJson = {
  groups: plan.groups.map((g, ix) => ({
    name: g.name,
    description: g.description,
    ...(g.notes ? { notes: g.notes } : {}),
    files: g.files,
    message: messages[ix].message,
  })),
  excluded: plan.excluded,
}

phase('Assemble')
await agent(
  `Install the git-group-commit artifacts (mechanical, no judgment). Skill folder: ${skillDir}${dirNote}.
1. GIT_DIR=$(git rev-parse --git-dir)
2. For EACH group below, compute its staleness fingerprint: sh ${skillDir}/scripts/group-commit.sh --hash <that group's files...> — then write the JSON to $GIT_DIR/commits.json exactly as given EXCEPT each group gains a "diffHash" field with its computed fingerprint:
${JSON.stringify(commitsJson, null, 2)}
3. cp <skill folder>/scripts/group-commit.sh "$GIT_DIR/group-commit.sh" && chmod +x "$GIT_DIR/group-commit.sh"
4. git config alias.group-commit '!sh "$(git rev-parse --git-dir)/group-commit.sh"'
5. Verify: git group-commit --dry-run --no-color exits 0. Do NOT commit anything.`,
  { model: 'haiku', effort: 'low', label: 'assemble', phase: 'Assemble' },
)

return {
  committedPlan: true,
  groups: commitsJson.groups.map((g, ix) => ({ n: ix + 1, name: g.name, files: g.files.length, header: g.message.split('\n')[0] })),
  excluded: plan.excluded,
  next: 'Review with `git group-commit --dry-run`, then run `git group-commit`.',
}
