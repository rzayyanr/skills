"""Integration tests using disposable local repositories, never user repositories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('preflight.py')
SCRATCH = Path(os.environ.get('UCR_TEST_SCRATCH', str(Path.home() / 'AppData/Local/hermes/cache/scratch')))

class PreflightTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='ucr-preflight-', dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo with spaces'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Review Test Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.hooks = self.root / 'empty-hooks'
        self.hooks.mkdir()
        self.git('config', 'core.hooksPath', self.hooks.as_posix())
        (self.repo / 'tracked.txt').write_text('baseline\n', encoding='utf-8')
        self.git('add', 'tracked.txt')
        self.git('commit', '-m', 'fixture baseline')
        self.head = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True, encoding='utf-8', stderr=subprocess.STDOUT)

    def run_check(self, expected=None, extra=()):
        self.assertTrue(SCRIPT.is_file(), 'preflight CLI is not implemented yet')
        proc = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.repo), '--expected-head', expected or self.head, '--base', 'main', *extra], capture_output=True, text=True, encoding='utf-8')
        return proc, json.loads(proc.stdout)

    def test_wrong_head_blocks_without_checkout_or_discard(self):
        (self.repo / 'tracked.txt').write_text('user work\n', encoding='utf-8')
        (self.repo / 'keep.txt').write_text('do not remove', encoding='utf-8')
        before = self.git('status', '--porcelain=v1')
        proc, data = self.run_check('a' * 40)
        self.assertEqual(proc.returncode, 1)
        self.assertIn('head_mismatch', data['blockers'])
        self.assertIn('safe_to_run_local_checks', data)
        self.assertFalse(data['safe_to_run_local_checks'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.head)
        self.assertEqual(self.git('status', '--porcelain=v1'), before)
        self.assertEqual((self.repo / 'tracked.txt').read_text(), 'user work\n')
        self.assertEqual((self.repo / 'keep.txt').read_text(), 'do not remove')

    def test_stale_base_blocks_even_when_head_matches(self):
        proc, data = self.run_check(extra=('--expected-base', 'b' * 40))
        self.assertEqual(proc.returncode, 1)
        self.assertIn('base_mismatch', data['blockers'])
        self.assertFalse(data['safe_to_run_local_checks'])

    def test_clean_revision_is_preflight_pass_but_runtime_unverified(self):
        proc, data = self.run_check(extra=('--expected-base', self.head))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data['preflight'], 'Pass')
        self.assertTrue(data['safe_to_run_local_checks'])
        self.assertFalse(data['runtime_suitable'])
        self.assertEqual(data['runtime']['status'], 'Not verified')
        self.assertEqual(data['local_head'], self.head)
        self.assertEqual(data['base_sha'], self.head)
        self.assertEqual(data['changed_files'], [])

    def test_dirty_worktree_blocks_without_head_mismatch(self):
        (self.repo / 'keep.txt').write_text('private local work', encoding='utf-8')
        proc, data = self.run_check()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(data['blockers'], ['dirty_worktree'])
        self.assertFalse(data['safe_to_run_local_checks'])
        self.assertTrue((self.repo / 'keep.txt').exists())

    def test_expected_base_is_optional_but_base_snapshot_unverified(self):
        proc, data = self.run_check()
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(data['expected_base'])
        self.assertEqual(data['base_identity'], 'Not verified')

    def test_malformed_expected_head_is_bad_input_not_mismatch(self):
        proc, data = self.run_check(expected='not-a-sha')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(data['error_code'], 'invalid_expected_head')
        self.assertFalse(data['safe_to_run_local_checks'])

    def test_malicious_base_revision_is_rejected_without_running_git_expression(self):
        proc, data = self.run_check(extra=('--base', 'main~1'))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(data['error_code'], 'invalid_base')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.head)

    def test_changed_files_only_from_base_to_head(self):
        self.git('branch', 'feature')
        self.git('switch', 'feature')
        (self.repo / 'new.txt').write_text('feature\n', encoding='utf-8')
        self.git('add', 'new.txt')
        self.git('commit', '-m', 'feature')
        head = self.git('rev-parse', 'HEAD').strip()
        proc, data = self.run_check(expected=head, extra=('--expected-base', self.head))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data['merge_base'], self.head)
        self.assertEqual(data['changed_files'], ['new.txt'])

    def test_non_repository_returns_structured_error_not_traceback(self):
        non_repo = self.root / 'outside'
        non_repo.mkdir()
        proc = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(non_repo),
                               '--expected-head', self.head, '--base', 'main'],
                              capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)['error_code'], 'command_or_repository_error')
        self.assertNotIn('Traceback', proc.stderr)

    def test_missing_args_returns_json_error(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True,
                              text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)['error_code'], 'invalid_arguments')

    def test_preflight_does_not_run_configured_fsmonitor_hook(self):
        marker = self.root / 'hook-ran.txt'
        hook = self.root / 'fsmonitor.sh'
        hook.write_text('#!/bin/sh\nprintf triggered > "' + marker.as_posix() + '"\n', encoding='utf-8')
        self.git('config', 'core.fsmonitor', hook.as_posix())
        proc, data = self.run_check()
        self.assertEqual(proc.returncode, 0, data)
        self.assertFalse(marker.exists(), 'Git fsmonitor hook must not run during preflight')

if __name__ == '__main__':
    unittest.main(verbosity=2)
