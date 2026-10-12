# Universal Code Review

> Created and maintained by Zayyan Rizka.

Universal Code Review is a platform-independent workflow for thoroughly reviewing coding changes before approval. It can be used for frontend, backend, full-stack, database, testing, infrastructure, configuration, and security-related work.

The workflow always performs a thorough review. It uses four internal modes: Intake, Full Review, Re-review, and Audit. The modes change the starting point and comparison context, not the quality standard.

## Core principles

1. Review the latest live state, not an old conversation snapshot.
2. Treat the issue or specification and its acceptance criteria as the primary source of truth.
3. Separate workflow compliance, specification compliance, code quality, security, automated checks, and runtime behavior.
4. A green CI result does not prove that the whole ticket is complete.
5. `Not verified` is not `Pass`.
6. Continue reviewing when a correctable workflow problem exists, such as a wrong base branch, but mark the result provisional and refresh after the correction.
7. Stop only when the target cannot be identified or the change cannot be inspected.
8. Never treat a developer's completion message as evidence by itself.
9. Separate blocking findings from optional suggestions.
10. Prepare drafts before writing to external systems and request human confirmation first.
11. Verify every external write by reading the exact target again.

## Internal modes

### Intake

Use when the issue, repository, pull request, branch, scope, or commit is missing or ambiguous.

Discover and record:

- Issue or ticket.
- Repository.
- Pull request or branch.
- Assignee.
- Scope.
- Target application or package.
- Latest commit.
- Base branch.

Completion criterion: the review target is clearly identified, or the missing context is reported.

### Full Review

Use for a first review, a large change, or any review without a trustworthy previous review.

Run every applicable procedure in this document.

Completion criterion: every applicable requirement and review phase has a status and evidence.

### Re-review

Use after a developer sends new commits or says that requested changes are complete.

Compare the current state with the previous review:

- Did every required finding get fixed?
- Is the fix correct?
- Did the fix create a regression?
- Did the scope change?
- Did the quality gates remain successful?
- Is the latest commit the one being reviewed?

If the base branch, merge base, or diff changes substantially, run a full review against the new state.

Completion criterion: every previous required change is classified as fixed, still failing, not verified, or no longer applicable, and new regressions are checked.

### Audit

Use when the reviewer asks whether a previous status, decision, comment, or review remains correct.

Verify the current state of:

- Issue.
- Pull request.
- Latest commit.
- Review decision.
- Open conversations.
- Checks.
- Acceptance criteria.
- Previous evidence.

Completion criterion: the current state and the validity of the previous decision are explicitly established.

## Complete review procedure

### 1. Create the review snapshot

Record:

```text
Issue:
Repository:
Pull request or branch:
Assignee:
Reviewer:
Review mode:
Latest commit:
Base branch:
Source branch:
Target application or package:
Review date:
Current status:
```

If multiple pull requests could match, do not guess. List the candidates and ask the reviewer to choose.

### 2. Refresh every source

Read the current versions of:

- Issue description.
- Scope and scope out.
- Acceptance criteria.
- Review plan.
- Definition of Done.
- Dependencies.
- Design references.
- Pull request description.
- Changed files.
- Commits.
- Previous reviews and comments.
- Open conversations.
- CI and automated checks.

Do not rely on information from an earlier review if the pull request may have changed.

### 3. Classify the change

Identify all applicable change types:

- Frontend UI.
- Frontend logic.
- Backend API.
- Full-stack integration.
- Database or migration.
- Testing.
- Infrastructure or CI/CD.
- Configuration or dependency.
- Security-sensitive change.
- Documentation-only change.

Use the relevant technical checks later in this document.

### 4. Build the requirement matrix

Convert every acceptance criterion into a verifiable row:

| Requirement | Evidence required | Status | Evidence location |
|---|---|---|---|
| ... | ... | Pass / Fail / Not verified / Not applicable / Blocked | ... |

Also record:

- Missing requirements.
- Scope creep.
- Contradictions with the specification.
- Ambiguous requirements.
- Claims in the pull request that lack evidence.

Do not mark runtime behavior as `Pass` from code reading alone.

### 5. Validate workflow and repository hygiene

Check:

- Pull request is open and accessible.
- Source branch is identifiable.
- Base branch follows repository rules.
- Branch naming follows repository conventions.
- Latest commit is known.
- Pull request is not a duplicate.
- Changed files stay within scope.
- No secrets, credentials, environment files, or local artifacts are included.
- Generated files follow repository rules.
- The branch is reasonably based on the current target branch.
- Unrelated tickets are not combined.

A wrong base branch does not automatically stop the review. Continue reviewing the available diff, record a workflow blocker, and mark the result provisional. After the branch is corrected, refresh the pull request and recheck the affected diff before a final decision.

Stop only if the pull request or diff cannot be inspected, the repository is inaccessible, or there is no usable specification.

### 6. Review specification compliance

Classify findings as:

- **Missing requirement:** requested behavior or artifact is absent.
- **Incorrect implementation:** present but does not satisfy the requirement.
- **Scope creep:** change is outside the ticket scope.
- **Contradiction:** conflicts with the specification, product decision, API contract, or documented rule.
- **Unverifiable claim:** completion is claimed without sufficient evidence.

For each finding, include the exact requirement, file or behavior involved, evidence, and required action.

### 7. Review dependencies and boundaries

Check:

- New dependencies are necessary.
- Dependencies are added to the correct application or package.
- Lockfiles match package manifests.
- Shared package changes are intentional.
- API consumers match the current contract.
- Generated files are not edited manually when prohibited.
- Frontend and backend types agree.
- Database and application assumptions agree.
- Configuration changes do not affect unrelated applications.
- A UI library or framework change does not silently expand to another application.

### 8. Review code quality and security

Inspect complete changed-file context, not only diff fragments.

Check:

- Correctness and edge cases.
- Type safety and null handling.
- External input validation.
- Error handling for I/O, network, database, and user actions.
- Authentication and authorization boundaries.
- Naming and module boundaries.
- Duplication and speculative abstraction.
- Debug output and commented-out code.
- Secrets and credential exposure.
- Injection risks.
- Unsafe evaluation.
- Path traversal.
- Unsafe deserialization.
- Unsafe HTML or script injection.
- Accessibility, keyboard behavior, semantic markup, responsive behavior, and focus states for UI changes.

Keep code-quality findings separate from specification blockers.

### 9. Run automated checks

Read the repository scripts before running commands. Do not invent command names.

Run applicable checks such as:

- Lint.
- Format check.
- Typecheck.
- Unit tests.
- Integration tests.
- End-to-end tests.
- Build.
- Repository-specific gates.
- Migration validation.
- Dependency or security checks.

Record:

```text
Command:
Exit code:
Result:
Important output:
Pre-existing or introduced failure:
```

A check that was not run must be marked `Not run`, not `Pass`.

### 10. Perform AI runtime verification

When the environment allows it, exercise the change directly.

#### Frontend

- Start the application.
- Open all named routes.
- Use navigation.
- Inspect console errors.
- Inspect network failures.
- Test responsive layout.
- Check loading, empty and error states.
- Check overflow and fixed elements.

#### Backend

- Start the service.
- Call valid inputs.
- Call invalid inputs.
- Test unauthorized access.
- Test not-found behavior.
- Check response shapes and status codes.
- Check error handling.

#### Full-stack

- Exercise the complete user path.
- Compare request and response contracts.
- Check authentication propagation.
- Check loading and error behavior.

#### Database

- Validate migrations in a safe environment.
- Check schema and constraints.
- Check data compatibility.
- Check rollback or recovery planning.

#### Infrastructure

- Validate configuration.
- Validate pipeline behavior.
- Check environment separation.
- Do not deploy or touch production without explicit authorization.

Never claim runtime verification if the command failed or the environment was unavailable.

### 11. Prepare human manual testing

Provide numbered instructions for checks that require human judgment or visual confirmation.

Every instruction must contain:

- Starting state.
- Exact action.
- Expected result.
- Evidence to capture if it fails.
- Browser, viewport, account, or environment when relevant.

Example:

```md
### Check: Mobile bottom navigation

1. Open the app at viewport 390 × 844.
2. Open the Home route.
3. Do not scroll.
4. Confirm that bottom navigation is visible.
5. Select Cart.
6. Confirm that the Cart route opens.
7. Confirm that navigation does not cover the content.

Expected: all steps work without crash, overflow, or console error.
Result: Pass / Fail / Not verified.
```

AI must not mark a human-only check as passed before the reviewer supplies the result or evidence.

### 12. Classify findings by severity

#### Blocker

Examples:

- Security issue.
- Build or CI failure.
- Broken critical behavior.
- Major scope violation.
- Data loss risk.
- Unsafe migration.
- Failed core acceptance criterion.
- Invalid review target.

#### Major

Examples:

- Important missing behavior.
- Incorrect API contract.
- Missing critical state.
- Serious accessibility failure.
- Requirement that needs substantial correction.

#### Minor

Examples:

- Naming.
- Limited duplication.
- Small documentation gap.
- Maintainability issue that does not affect the ticket outcome.

#### Informational

Examples:

- Future refactor.
- Optional optimization.
- Observation outside current scope.

Required changes and optional suggestions must be listed separately.

### 13. Recommend the review decision

Use exactly one recommendation:

- **Approve:** no blockers or majors, required criteria pass, required gates pass, and required manual checks are verified.
- **Request changes:** at least one blocker or major exists, or a required gate fails.
- **Pending verification:** the implementation is not proven wrong, but important evidence is missing.
- **Comment only:** only minor or informational findings exist.

A provisional review caused by a wrong base branch cannot be approved until the corrected diff is refreshed and verified.

### 14. Produce the complete report

Use this order:

1. Review metadata and mode.
2. Executive recommendation.
3. Review snapshot and commit.
4. Workflow checks.
5. Requirement matrix.
6. Scope and boundary review.
7. Code quality and security findings.
8. Automated checks.
9. AI runtime verification.
10. Human manual testing instructions and results.
11. Required changes by severity.
12. Non-blocking suggestions.
13. Remaining uncertainty and assumptions.
14. Draft code-host review.
15. Draft issue-tracker comment.
16. Draft developer message.
17. Confirmation request.

### 15. Confirm before writing externally

Show the drafts and ask the human reviewer to choose:

```text
Send as drafted
Revise the draft
Keep unsent
```

Do not submit approval, request changes, comments, status changes, assignment changes, relationship changes, or merges before explicit confirmation.

### 16. Verify every external write

After a confirmed write, read the exact target again and verify:

- Comment or review body.
- Review state.
- Inline comment location.
- Conversation state.
- Issue comment or description.
- Status, assignee, and relationship if explicitly changed.

Report the returned URL, identifier, or exact state. If verification fails, say so and do not claim success.

### 17. Repeat the review after fixes

When fixes arrive:

1. Refresh the issue, pull request, commit, checks, comments, and conversations.
2. Compare the new diff with the previously reviewed commit.
3. Map every old finding to fixed, still failing, not verified, or no longer applicable.
4. Check for regressions and unrelated new changes.
5. Rerun affected checks.
6. Repeat affected manual tests.
7. Produce a new complete report.

Never treat a developer's message saying “fixed” as proof.

### 18. Offer note storage

After presenting the complete report, ask:

> Apakah hasil review ini ingin disimpan ke Obsidian atau aplikasi catatan lain?

If yes, ask for or resolve the concrete folder and filename before writing. Preserve the ticket, pull request, commit, date, findings, evidence, decision, and re-review history. Do not restructure the user's notes without permission.

## Technical review adapters

### Frontend

Check routes, navigation, runtime crashes, console errors, network failures, responsive layout, overflow, fixed elements, loading, empty and error states, accessibility, keyboard and focus behavior, design references, and whether UI dependencies are configured and actually used.

### Backend

Check validation, authentication, authorization, response shape, status codes, error handling, idempotency, transaction boundaries, concurrency, logging, privacy, and tests for invalid and unauthorized inputs.

### Full-stack

Check the complete user path, API contract alignment, serialization, authentication propagation, loading states, error states, and whether both sides work together from the documented setup.

### Database

Check migration ordering, reversibility or recovery, constraints, indexes, backfill safety, nullability, existing data compatibility, transaction safety, and production impact.

### Testing

Check determinism, meaningful assertions, edge cases, failure behavior, isolation, fixture quality, naming, and whether tests exercise the intended behavior instead of only passing superficially.

### Infrastructure and configuration

Check environment separation, secrets, permissions, deployment target, rollback or recovery, pipeline conditions, dependency changes, reproducibility, and accidental changes to unrelated applications.

## Output rules

- Use concrete evidence and exact paths, commands, commit SHAs, and URLs when available.
- Never invent test output, browser behavior, API responses, or review state.
- State assumptions explicitly.
- Never hide a blocker among suggestions.
- Keep technical details on the code-host platform, concise status on the issue tracker, and notification text in chat.
- Avoid em dash characters; use normal punctuation instead.

## Common pitfalls

- Reviewing an old commit after new work has been pushed.
- Treating CI success as full approval.
- Treating a developer completion message as evidence.
- Stopping at the first correctable workflow error instead of recording it and continuing.
- Approving while important criteria remain `Not verified`.
- Mixing out-of-scope changes into an otherwise correct review.
- Sending a draft without confirmation.
- Reusing a screenshot or test result from an earlier commit.
- Changing issue status or relationships as an automatic side effect.

## Final verification checklist

- [ ] Correct issue, repository, PR, branch, and latest commit are recorded.
- [ ] Current issue-tracker and code-host state was refreshed.
- [ ] Scope, scope out, and acceptance criteria are mapped.
- [ ] Workflow checks are complete.
- [ ] Full changed-file context was inspected.
- [ ] Applicable security and dependency checks were performed.
- [ ] Applicable lint, typecheck, test, build, and repository gates were run.
- [ ] Runtime verification was attempted or its limitation is stated.
- [ ] Human manual testing instructions are precise.
- [ ] Findings are separated by severity.
- [ ] Required changes are separated from suggestions.
- [ ] Recommendation follows the decision rules.
- [ ] Drafts were shown before external writes.
- [ ] Authorized external writes were read back and verified.
- [ ] The reviewer was asked whether to save the report to notes.
