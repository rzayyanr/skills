# Revision preflight

Run before local checks or runtime review. This CLI is read-only with respect to the repository. Use an isolated checkout or worktree when possible. It does not contact GitHub or check branch protection, and cannot certify a running server's checkout, port or tested URL.

```bash
python scripts/preflight.py --repo <absolute-local-path> --expected-head <full-pr-head-sha> --base <local-base-ref-or-full-sha> --expected-base <full-live-base-sha>
```

First fetch/update local references separately only if explicitly permitted. The script never fetches, resets, checks out, installs, starts/stops processes or writes the review. `--expected-base` is optional for offline inspection, but omitting it leaves `base_identity: Not verified`; the current local base is not proof of the live remote base.

Machine-readable JSON on stdout, exit codes:
- `0`: clean worktree, local HEAD matches supplied full SHA; supplied base snapshot matches if given. `safe_to_run_local_checks` true.
- `1`: blocked due to head mismatch, base mismatch or dirty worktree. Preserve the files and investigate; do not force checkout or clean.
- `2`: bad input or unavailable Git repository. See `error_code`; child stderr is intentionally not printed.

Output includes local/base/merge-base SHA, changed paths and porcelain status. This is local preflight only: `runtime_suitable` stays false, and `runtime.status` stays `Not verified` until a reviewer separately records and verifies the actual server process, working directory, live port, URL, and revision. If local tests regenerate tracked files, collect original state and isolate generated output. Passing preflight never means a PR is approved.

Run its disposable tests from the skill directory:

```bash
python scripts/test_preflight.py
```

Tests create and remove only their own repositories under the Hermes scratch directory (override with `UCR_TEST_SCRATCH`). They verify mismatched revision, dirty preservation, stale base, malformed input, changed files, and disabled configured fsmonitor hooks. These tests demonstrate CLI behavior only, not that an agent always follows the skill.
