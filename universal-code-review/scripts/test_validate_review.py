"""Synthetic metadata fixtures only; no real PR or evidence verification."""
import copy
import base64
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('validate_review.py')
HEAD = 'a' * 40
BASE = 'b' * 40
ARTIFACT = b'Synthetic validator test artifact. Not real review proof.\n'
PIXEL = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9p7o4x8AAAAASUVORK5CYII=')
SCRATCH = Path(os.environ.get('TMPDIR') or Path.home() / 'AppData/Local/hermes/cache/scratch') / 'ucr-upgrade/validator'


def record(identifier='REQ-1'):
    return {'id': identifier, 'mandatory': True, 'status': 'Not verified',
            'method': 'Static', 'expected': 'Synthetic expected behavior', 'actual': 'Not exercised',
            'revision': HEAD, 'evidence_refs': []}


def pending():
    return {'schema_version': 1, 'target': {'head_sha': HEAD, 'base_sha': BASE,
            'tested_merge_sha': None}, 'reviewed_at': '2026-10-14T03:00:00+07:00',
            'mode': 'Full Review', 'recommendation': 'Pending verification',
            'collection': {'complete': False, 'items': [
                {'id': 'COL-1', 'name': 'Synthetic diff', 'complete': False,
                 'expected_count': 1, 'collected_count': 0}]},
            'requirements': [record()], 'checks': [record('CHK-1')],
            'evidence': [], 'findings': [], 'exceptions': [],
            'extensions': {'synthetic': True}}


def passing():
    value = pending()
    value['collection']['complete'] = True
    value['collection']['items'][0].update(complete=True, collected_count=1)
    value['evidence'] = [{'id': 'EV-1', 'kind': 'Static', 'revision': HEAD,
                          'base_sha': BASE, 'location': 'artifact.log',
                          'sha256': hashlib.sha256(ARTIFACT).hexdigest(),
                          'captured_at': '2026-10-14T03:00:00+07:00',
                          'summary': 'Synthetic fixture, not proof'}]
    for row in value['requirements'] + value['checks']:
        row.update(status='Pass', actual='Synthetic observed outcome', evidence_refs=['EV-1'])
    return value


def approvable():
    value = passing()
    value['recommendation'] = 'Approve'
    return value


class ReviewTests(unittest.TestCase):
    def run_cli(self, data=None, raw=None, args=None, setup=None):
        self.assertTrue(SCRIPT.is_file(), 'validation CLI has not been implemented')
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='synthetic-review-', dir=SCRATCH) as folder:
            (Path(folder) / 'artifact.log').write_bytes(ARTIFACT)
            (Path(folder) / 'pixel.png').write_bytes(PIXEL)
            if setup is not None:
                setup(Path(folder))
            fixture = Path(folder) / 'synthetic-review.json'
            fixture.write_text(raw if raw is not None else json.dumps(data), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), *(args if args is not None else ['--file', str(fixture)])], capture_output=True, text=True)
        self.assertNotIn('Traceback', result.stderr + result.stdout)
        self.assertEqual(result.stderr, '')
        output = json.loads(result.stdout)
        self.assertEqual(output['valid'], result.returncode == 0)
        self.assertEqual(output['evidence_verified'], False)
        self.assertIsInstance(output['errors'], list)
        return result.returncode, output

    def test_structure_rejects_missing_unknown_and_wrong_types(self):
        examples = [None, [], True, 1, 'review']
        for key in pending():
            if key != 'extensions':
                value = pending()
                del value[key]
                examples.append(value)
        for path, bad_values in [
            (('schema_version',), [True, 0, 2, '1', 1.0]),
            (('mode',), ['Review', [], None]),
            (('recommendation',), ['approved', {}, None]),
            (('target',), [[], None, 'head']),
            (('target', 'head_sha'), ['a' * 39, 'a' * 41, ' ' + HEAD, HEAD + '\n', 'g' * 40, 123]),
            (('target', 'base_sha'), ['short', None]),
            (('collection', 'complete'), [1, 'true', None]),
            (('collection', 'items', 0, 'expected_count'), [-1, True, 1.0, '1']),
            (('requirements', 0, 'mandatory'), [1, 'true', None]),
            (('requirements', 0, 'status'), ['Success', [], None]),
            (('requirements', 0, 'expected'), ['', '  ', [], None]),
            (('requirements', 0, 'evidence_refs'), ['E-1', [1], [None], [{}]]),
            (('checks',), [{}, None]),
            (('findings',), [{}, [None], [True], [[]]]),
            (('evidence',), [{}, [None], [[]]]),
            (('exceptions',), [{}, [None], [[]]]),
            (('extensions',), [[], None, True])]:
            for bad in bad_values:
                value = pending()
                node = value
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = bad
                examples.append(value)
        for path in [(), ('target',), ('collection',), ('collection', 'items', 0), ('requirements', 0)]:
            value = pending()
            node = value
            for part in path:
                node = node[part]
            node['typo'] = True
            examples.append(value)
        for index, value in enumerate(examples):
            with self.subTest(index=index, value=value):
                code, result = self.run_cli(value)
                self.assertEqual(code, 1, result)
                self.assertTrue(result['errors'])

    def test_pass_requires_revision_bound_existing_evidence(self):
        self.assertEqual(self.run_cli(passing())[0], 0)
        cases = []
        for change in ['missing', 'unknown', 'duplicate-ref', 'stale-record', 'stale-evidence', 'stale-base', 'duplicate-id', 'cross-kind-id']:
            value = passing()
            row = value['requirements'][0]
            if change == 'missing':
                row['evidence_refs'] = []
            elif change == 'unknown':
                row['evidence_refs'] = ['NOT-FOUND']
            elif change == 'duplicate-ref':
                row['evidence_refs'] *= 2
            elif change == 'stale-record':
                row['revision'] = BASE
            elif change == 'stale-evidence':
                value['evidence'][0]['revision'] = BASE
            elif change == 'stale-base':
                value['evidence'][0]['base_sha'] = HEAD
            elif change == 'duplicate-id':
                value['evidence'].append(copy.deepcopy(value['evidence'][0]))
            elif change == 'cross-kind-id':
                row['id'] = 'EV-1'
            cases.append((change, value))
        for change, value in cases:
            with self.subTest(change=change):
                self.assertEqual(self.run_cli(value)[0], 1)

    def test_evidence_schema(self):
        for key in passing()['evidence'][0]:
            value = passing()
            del value['evidence'][0][key]
            with self.subTest(missing=key):
                self.assertEqual(self.run_cli(value)[0], 1)
        for field, bad in [('kind', 'Screenshot'), ('revision', 'short'), ('base_sha', None), ('id', []), ('location', ''), ('summary', {}), ('typo', True)]:
            value = passing()
            value['evidence'][0][field] = bad
            with self.subTest(field=field):
                self.assertEqual(self.run_cli(value)[0], 1)

    def test_artifacts_are_local_contained_and_hash_verified(self):
        self.assertEqual(self.run_cli(passing())[0], 0)
        for field, bad in [
            ('location', 'missing.log'), ('location', '.'),
            ('location', '../artifact.log'), ('location', 'nested/../../artifact.log'),
            ('location', '/artifact.log'), ('location', 'C:\\artifact.log'),
            ('location', '..\\artifact.log'), ('location', 'artifact.log:stream'),
            ('location', 'https://example.invalid/log'),
            ('sha256', '0' * 64), ('sha256', 'short'), ('sha256', None)]:
            value = passing()
            value['evidence'][0][field] = bad
            with self.subTest(field=field, bad=bad):
                code, result = self.run_cli(value)
                self.assertEqual(code, 1, result)
                self.assertTrue(result['errors'])

    def test_symlink_escape_is_rejected_when_platform_supports_it(self):
        with tempfile.TemporaryDirectory(prefix='synthetic-external-', dir=SCRATCH) as outside:
            target = Path(outside) / 'external.log'
            target.write_bytes(ARTIFACT)
            def link(folder):
                try:
                    os.symlink(target, folder / 'linked.log')
                except OSError as exc:
                    self.skipTest(f'filesystem does not permit symlinks: {type(exc).__name__}')
            d = passing()
            d['evidence'][0]['location'] = 'linked.log'
            self.assertEqual(self.run_cli(d, setup=link)[0], 1)

    def test_bad_input_is_json_exit_two(self):
        for raw in ['{', '', '{"schema_version": 1, "schema_version": 1}', 'NaN', 'Infinity', '1e999']:
            with self.subTest(raw=raw):
                code, result = self.run_cli(raw=raw)
                self.assertEqual(code, 2, result)
                self.assertTrue(result['errors'])
        for args in [[], ['--file', 'nonexistent-review-fixture.json'], ['--unknown']]:
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(raw='{}', args=args)[0], 2)

    def test_approve_requires_complete_collection_and_all_mandatory_pass(self):
        self.assertEqual(self.run_cli(approvable())[0], 0)
        for mutate in [
            lambda d: d['collection'].update(complete=False),
            lambda d: d['collection']['items'][0].update(collected_count=0),
            lambda d: d['collection']['items'][0].update(complete=False),
            lambda d: d['requirements'][0].update(status='Not verified'),
            lambda d: d['checks'][0].update(status='Fail'),
            lambda d: d['checks'][0].update(status='Not applicable'),
            lambda d: d.update(checks=[]),
            lambda d: d.update(requirements=[]),
        ]:
            d = approvable()
            mutate(d)
            with self.subTest(case=d):
                self.assertEqual(self.run_cli(d)[0], 1)

    def test_unresolved_major_or_blocker_forbids_approve(self):
        for severity in ('Major', 'Blocker'):
            d = approvable()
            d['findings'] = [{'id': 'F-1', 'severity': severity, 'origin': 'Introduced',
                              'status': 'Open', 'revision': HEAD, 'description': 'Synthetic issue',
                              'evidence_refs': ['EV-1']}]
            with self.subTest(severity=severity):
                self.assertEqual(self.run_cli(d)[0], 1)
            d['findings'][0]['status'] = 'Resolved'
            self.assertEqual(self.run_cli(d)[0], 0)

    def test_exception_cannot_make_unverified_mandatory_item_pass(self):
        d = approvable()
        d['requirements'][0]['status'] = 'Not verified'
        d['exceptions'] = [{'id': 'EX-1', 'owner': 'Owner', 'rationale': 'Delayed evidence',
                            'scope': 'REQ-1', 'residual_risk': 'Unknown layout',
                            'record_ids': ['REQ-1'], 'approved_at': '2026-10-14T10:00:00+07:00'}]
        self.assertEqual(self.run_cli(d)[0], 1)
        d['recommendation'] = 'Pending verification'
        self.assertEqual(self.run_cli(d)[0], 0)

    def test_visual_requirement_rejects_http_or_dom_evidence(self):
        d = approvable()
        d['requirements'][0]['method'] = 'Visual'
        d['requirements'][0]['evidence_refs'] = ['EV-2']
        artifact = copy.deepcopy(d['evidence'][0])
        artifact.update(id='EV-2', kind='Visual', location='pixel.png',
                        sha256=hashlib.sha256(PIXEL).hexdigest())
        d['evidence'].append(artifact)
        for kind in ('Static', 'Automated', 'Runtime', 'Human'):
            d['evidence'][1]['kind'] = kind
            with self.subTest(kind=kind):
                self.assertEqual(self.run_cli(d)[0], 1)
        d['evidence'][1]['kind'] = 'Visual'
        self.assertEqual(self.run_cli(d)[0], 0)
        d['evidence'][1]['location'] = 'artifact.log'
        d['evidence'][1]['sha256'] = hashlib.sha256(ARTIFACT).hexdigest()
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_explicit_merge_result_revision_is_allowed(self):
        d = approvable()
        merge_sha = 'c' * 40
        d['target']['tested_merge_sha'] = merge_sha
        for row in d['requirements'] + d['checks']:
            row['revision'] = merge_sha
        d['evidence'][0]['revision'] = merge_sha
        self.assertEqual(self.run_cli(d)[0], 0)
        d['target']['tested_merge_sha'] = None
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_timestamps_must_include_timezone_and_be_valid(self):
        for value in ('2026-10-14T03:00:00', '2026-13-14T03:00:00+07:00',
                      'yesterday', '', None, 123):
            d = passing()
            d['evidence'][0]['captured_at'] = value
            with self.subTest(value=value):
                self.assertEqual(self.run_cli(d)[0], 1)
        d = passing()
        d['reviewed_at'] = '2026-10-14T03:00:00'
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_all_pass_rows_must_use_current_head_or_declared_merge(self):
        d = approvable()
        d['checks'][0]['mandatory'] = False
        d['checks'][0]['revision'] = BASE
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_invalid_exception_timestamp_and_unknown_record_are_rejected(self):
        for when in ('2026-10-14T03:00:00', 'not-a-date'):
            d = pending()
            d['exceptions'] = [{'id': 'EX-1', 'owner': 'Owner', 'rationale': 'Scope waiver',
                                'scope': 'REQ-1', 'residual_risk': 'Unknown',
                                'record_ids': ['REQ-1'], 'approved_at': when}]
            with self.subTest(when=when):
                self.assertEqual(self.run_cli(d)[0], 1)
        d['exceptions'][0]['approved_at'] = '2026-10-14T03:00:00+07:00'
        d['exceptions'][0]['record_ids'] = ['missing-row']
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_future_evidence_cannot_support_earlier_review(self):
        d = passing()
        d['evidence'][0]['captured_at'] = '2026-10-15T03:00:00+07:00'
        self.assertEqual(self.run_cli(d)[0], 1)

    def test_unsupported_request_changes_without_failed_item_or_finding_is_rejected(self):
        d = approvable()
        d['recommendation'] = 'Request changes'
        self.assertEqual(self.run_cli(d)[0], 1)
        d['checks'][0]['status'] = 'Fail'
        self.assertEqual(self.run_cli(d)[0], 0)

    def test_failed_mandatory_gate_cannot_be_pending_verification(self):
        d = passing()
        d['checks'][0]['status'] = 'Fail'
        self.assertEqual(self.run_cli(d)[0], 1)
        d['recommendation'] = 'Request changes'
        self.assertEqual(self.run_cli(d)[0], 0)

    def test_valid_pending_verification(self):
        code, result = self.run_cli(pending())
        self.assertEqual(code, 0, result)
        self.assertEqual(result['errors'], [])


if __name__ == '__main__':
    unittest.main()
