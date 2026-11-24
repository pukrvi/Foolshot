# Foolshot research

Before reviewing new X threads or downloading linked projects, read the [research overview](offline-research/README.md) and the [resource review register](offline-research/resources/INDEX.md).

- Reuse existing notes by X post ID and existing repositories by upstream owner and name.
- Use the register’s do-not-download list to skip reviewed rejects and duplicate snapshots. Revisit a reject only when new evidence addresses its recorded reason or Foolshot’s needs change.
- Record each new review with its source, date, decision, and reason. Add new evidence to the existing entry for a project or thread already covered.
- Keep review decisions in the register when source snapshots go into `offline-research/resources/delete/`.

## Foolshot project memory

Capture every Foolshot user prompt verbatim using the project UserPromptSubmit hook. If the client has no active hook, use scripts/study note under a chat session with a stable message ID before acting. Keep secrets in credential settings. Read relevant prior owner_decision, lesson and review records before new work. Record explicit decisions separately from suggestions. For a trade, record the public decision rationale, evidence, expected invalidation, action and result. For a revision, append a dated correction. Runtime data stays private on this machine.

Start with docs/research/study-protocol.md for the learning experiment, docs/decisions/Foolshot_Alignment_Log.md for owner intent, and README.md for commands. Use scripts/cohort for matched adaptive and frozen runs. Keep hypothesis revisions, evidence, test outcomes and owner steering append-only. Report both improved and degraded results.

## Model orchestration and authorship

Use the newest available Astra in Codex or Fable in Claude Code for hypotheses, all trade/pass decisions, forecasts, incident diagnoses, weekly dreaming and trial judgments. Use Sol or Opus for day-to-day operational summaries, evidence preparation and reporting. Keep arithmetic, routing, accounting and risk enforcement in code. Routine summaries may flag evidence for review. They cannot originate trade instructions or new strategies. An unavailable thinking model blocks its decision.

Use the shared harness router for each model call. Preserve exact model selection and receipt evidence. Record Puneet Vishnawat on his steering and decisions. For assistant-authored notes, supply the exact author release. Keep execution actor, decision author, UTC recording time, source time where available, and evidence IDs distinct. Reuse completed responses and send compact evidence. Preserve the original full evidence locally.

## GitHub issue and PR workflow

Every new implementation, fix, research deliverable, or proposed harness change starts with a GitHub issue in the private `pukrvi/Foolshot` repository. This includes requests received in chat, findings from reviews, and work initiated by agents. Search open issues first and update an existing matching issue. Record the request, rationale, scope, acceptance criteria, and relevant evidence references without uploading private runtime data or secrets.

At the start of each project session, check the open issue and PR queues. Prioritize owner-assigned work, blockers, then approved backlog items. Before taking an issue, confirm it is unclaimed and comment with the plan. Branch from current main using `issue-<number>-<slug>`. Keep commits focused and reference the issue number. Test the change, then open a PR with `Closes #<number>`, a summary, verification results, and rollback implications. Report the PR and leave review and merge to the applicable owner authorization. Preserve failed proposals and their test evidence in the issue. If GitHub access is unavailable, report the blocker and retain the request locally for later filing.

Check the backlog daily at 08:30 IST and during the weekly review. Use review findings to create scoped candidate issues for human consideration. Scheduled checks may report the queue and draft proposals. Never let a backlog item bypass required review or authorize live account actions. See [workflow](docs/development-workflow.md).
