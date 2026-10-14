# Domain-specific review checks

Load for every Full Review and select applicable sections; record exclusions with reasons. In Re-review load sections affected by the delta. Read complete changed-file context and relevant callers/contracts, not only diff hunks.

## Shared quality and security

Check correctness, boundary values, null/undefined handling, input validation, errors, authorization, naming, module boundaries, duplication and unnecessary abstractions. Look for debug output, secret exposure, injection, unsafe evaluation/HTML, path traversal and insecure deserialization. Trace external input to sensitive operations. Redact secret values in reports. Scope dependency changes to the proper package, verify manifests/lockfiles and inspect generated-file rules. Avoid manually changing generated API contracts.

## Frontend

- Verify actual routes, navigation and component usage, not just exports. Exercise initial viewport, middle/end scrolling, route transitions, reload and back/forward as relevant.
- Check persistent navigation, content occlusion, safe-area behavior and focus visibility separately from horizontal overflow.
- Use a mobile baseline such as 390 x 844 and a narrower viewport such as 320 x 700 when relevant; record actual viewport, browser and zoom. Test wide layout if in scope.
- Check loading, empty, error, success, long text, missing/broken images, disabled controls, and real empty input where required. Forced mock-state labels do not prove automatic empty-data handling.
- Scope DOM assertions to the component under test; global skeleton counts include unrelated placeholders. Accessible labels need not appear in innerText.
- Inspect screenshots directly, not just dimensions. Inspect console errors and failed network requests and classify pre-existing/environmental failures honestly.
- Check semantic elements, accessible names, keyboard navigation, focus management and error/status announcements as applicable.
- Compare design intent with actual reference material. Do not infer pixel-perfect requirements from unspecified design details.

## Backend and full-stack

Check validation, authentication, authorization, response contracts/status codes, error handling, idempotency, concurrency, transaction boundaries, logging/privacy, and invalid/unauthorized requests. Trace consumers across serialization and API boundaries. Exercise relevant end-to-end paths where services are available; disclose unavailable dependencies rather than synthesizing responses as real evidence.

## Database

Check migration ordering, compatibility, constraints, indexes, backfill behavior, reversibility/recovery and data-loss risk. Validate in an isolated disposable environment. Do not run production migrations or destructive tests as review preparation.

## Tests

Check meaningful assertions, determinism, isolation, edge cases, failure paths and fixture quality. A passing test that never reaches the changed behavior is insufficient. Separate unit, integration, build, runtime and human evidence. Label reviewer-created probes and do not edit tracked tests without permission.

## Infrastructure and configuration

Check environment separation, permissions/secrets, dependency/action changes, event/branch conditions, deployment targets, reproducibility and rollback. Read workflow scripts to identify what actually ran. GitHub Actions and local Git hooks are different execution stages.

For changelog/attribution gates, apply repository policy rather than assuming human entries are optional or AI entries mandatory. Coauthor trailers and tags are policy signals, not proof of authorship. Test permitted human behavior, valid AI metadata, missing/invalid metadata and mixed contributions where applicable. Replay the actual script in its real shell mode against the relevant diff. Guard expected no-match branches without suppressing genuine failures with broad error ignores. Read configured Git identity before writing attributed entries in an authorized repair.
