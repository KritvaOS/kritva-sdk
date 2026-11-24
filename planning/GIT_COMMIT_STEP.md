# Kritva SDK Git and Commit Procedure

1. Fetch main and create a task-scoped branch.
2. Make one logical change per commit.
3. Use `type(scope): summary` with exactly one `Task:` or `Tasks:` footer.
4. Docs/chore changes implementing no task use `Tasks: None (reason)`.
5. Run applicable checks; report NOT_IMPLEMENTED gates explicitly.
6. Open a PR against main using `.github/PULL_REQUEST_TEMPLATE.md`.
7. Include task, milestone, scope, tests, immutable evidence, risks and pending work.
8. Do not close a milestone based only on merge, tag or CI pass.

Actual CI enforcement is authoritative; this document does not claim workflows are already installed.
