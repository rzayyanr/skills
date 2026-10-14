# Review evidence and consistency validator

Use the starter `templates/review.json`. Replace every `REPLACE_WITH_...` placeholder with an actual full SHA or timezone-aware timestamp, and add actual requirements, checks and evidence from the review. The starter is intentionally `Pending verification` with no invented evidence and fails validation until target identities are supplied.

CLI:

```bash
python scripts/validate_review.py --file C:/absolute/path/review.json
```

Prints JSON to stdout. Exit 0 means the record is internally consistent, exit 1 means inconsistent record, exit 2 means malformed JSON/CLI or missing input. This does **not** prove evidence is genuine, UI is visually correct, acceptance criteria are complete, a PR is approved, or a merge is authorized. A synthetic record with fabricated but internally consistent data may validate; the reviewer must inspect and authenticate evidence against the live PR.

## Format (schema_version 1)

- `target.head_sha` and `base_sha`: full 40-character Git SHAs. `tested_merge_sha`: explicit full SHA for an evaluated merge result, or null. A pass can reference the head or declared merge result, but must not silently use another revision.
- `reviewed_at`: timezone-aware ISO-8601 timestamp, e.g. `2026-10-14T09:00:00+07:00`.
- `mode`: `Intake`, `Full Review`, `Re-review`, or `Audit`; `recommendation`: `Approve`, `Request changes`, `Pending verification`, or `Comment only`.
- `collection`: `complete` plus items with unique ID/name, `expected_count`, `collected_count`, and `complete`. If counts disagree, mark incomplete and investigate; this only checks your asserted counts, not remote pagination.
- `requirements` / `checks`: each has unique `id`, `mandatory` boolean, `status`, `method`, `expected`, `actual`, `revision`, and `evidence_refs` array. Methods: `Static`, `Automated`, `Runtime`, `Visual`, `Human`. Statuses: `Pass`, `Fail`, `Not verified`, `Blocked`, `Not applicable`, `Not run`, `Not available`.
- `evidence`: each has `id`, `kind` (same method vocabulary), `revision`, `base_sha`, `location`, `sha256`, `captured_at`, `summary`. Location is a relative file under the review JSON directory (e.g. `evidence/loading.png`), not an arbitrary URL or a path outside the record. Copy external evidence only when authorized, save unique artifacts per scenario, inspect them, and record their hashes. Symlink/path escapes, missing files and checksum mismatches are rejected. Visual kind accepts PNG/JPEG/WebP signatures only; image validity and displayed content still require human inspection.
- `findings`: each has unique `id`, `severity` (`Blocker`, `Major`, `Minor`, `Informational`), `origin` (`Introduced`, `Regression`, `Pre-existing`, `Uncertain`), `status` (`Open`, `Resolved`), `revision`, `description`, `evidence_refs`. An unresolved major or blocker prevents `Approve`.
- `exceptions`: each has unique `id`, `owner`, `rationale`, `scope`, `residual_risk`, `record_ids`, `approved_at` (timezone-aware timestamp). An exception is explicit context, not a pass; an unverified mandatory item still prevents `Approve`.

`Approve` requires complete collection and nonempty requirement/check arrays with all mandatory rows `Pass`, matching evidence and no open major/blocker. A failed mandatory item or open major/blocker cannot be labeled `Pending verification`. `Request changes` needs a failed/blocked mandatory item or open major/blocker. `Comment only` is advisory. Other domain rules and repository policy remain the human reviewer's responsibility.

Test the validator using disposable synthetic artifacts under the Hermes scratch directory:

```bash
python scripts/test_validate_review.py
```

These unit/integration tests exercise parsing, type validation, checksums, path containment, revision binding, decision consistency and exceptions. They are **tool tests**, not proof that an agent follows the review skill in an unscripted case; see `references/skill-evaluation.md` for observed agent evaluations.
