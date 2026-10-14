# Release promotion review

Use for promotion between long-lived branches, such as staging to main. Apply core safety/evidence gates first.

## Pin the batch

Record source and target SHAs, merge base, actual ahead/behind results, effective file diff, linked feature PRs, and unresolved findings. Verify pagination before saying all PRs or files were examined. A behind count alone does not establish a conflict. Use a disposable checkout for merge simulation, without touching the user's active worktree or server.

## Evaluate the combined change

- Review the complete promotion diff, including workflow, hooks, dependency, lockfile, environment and generated-file changes not covered by feature reviews.
- Map requirements to actual scope. Do not imply work on an application merely because the workspace build includes it.
- Carry forward known bugs, waived criteria, missing evidence and open conversations even when feature PRs were merged or tickets marked Done.
- Run applicable batch checks on the source revision and, where needed, the proposed merge result. Label which was tested.
- Exercise affected routes and cross-feature paths; check console/network failures, navigation persistence, scrolling, content occlusion and responsive states.
- Identify mocks, placeholders, disabled/incomplete features and whether they are acceptable for the intended release audience.
- Read actual deployment configuration before claiming merge triggers production. Review relevant configuration, secrets handling, migrations, rollout and rollback without deploying during review.
- Resolve who opens, reviews and merges the promotion PR. Do not assume feature squash strategy applies to long-lived branch promotion.

## State the readiness level

1. Ready to open a PR: the batch can be presented for review, with known limitations disclosed. A draft PR may be appropriate when checks or evidence are incomplete.
2. Ready to merge: required review, relevant checks, integration evidence and repository policy requirements are satisfied, or an authorized exception is documented separately.
3. Ready for production: deployment-specific requirements and release acceptance are verified. If these are outside scope or inaccessible, state Not verified.

Do not collapse these into a single '100% ready' claim. Opening a PR, merging, and deployment are separate side effects requiring appropriate authorization.
