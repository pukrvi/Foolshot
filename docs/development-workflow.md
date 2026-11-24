# Development workflow

Repository target: private `pukrvi/Foolshot`.

## Issue lifecycle

1. Search the issue queue with `gh issue list --state open` and review existing PRs with `gh pr list`. Reuse an existing matching issue.
2. File each new request as an issue. Include task scope, owner intent, acceptance tests and relevant trace IDs. Use redacted summaries of private evidence.
3. Confirm ownership, then create `issue-<number>-<slug>` from current main. Keep separate workstreams isolated.
4. Implement and verify. Run `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` for the Python harness. Record actual results and any blocked checks.
5. Commit with the issue number, push the branch, and open a PR with `Closes #<number>`. Include scope, tests, limitations and rollback details. Respect review requirements before merging.
6. Record the final PR and commit identifiers in relevant study notes. Keep closed issues available for historical review.

## Queue cadence

- 08:30 IST each day: inspect open issues, blockers, active PRs and outstanding owner requests. Report a prioritized queue.
- Start of each project session: refresh the queue before claiming a task.
- Weekly review: translate evidence-backed findings into candidate issues, identify duplicates and record the proposed test. Changes to model selection, risk policy or research protocol require explicit review before adoption.

Private runtime databases, credentials, downloaded source trees and disposable research caches remain excluded from Git. When access is unavailable, retain owner requests locally and file them after access returns. The daily queue check is a development workflow, independent of market hours.
