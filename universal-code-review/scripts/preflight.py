"""Read-only revision preflight; never a review approval or runtime identity check."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

SHA = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})')


class PreflightError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PreflightError('invalid_arguments')


def git(repo, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '--no-optional-locks',
                             '-C', str(repo), *args],
                            env=env, capture_output=True, check=True, timeout=30)
    return result.stdout.decode('utf-8', errors='surrogateescape')


def resolve_base(repo, token):
    if SHA.fullmatch(token):
        resolved = git(repo, 'rev-parse', '--verify', '--end-of-options', token + '^{commit}').strip()
        if resolved != token:
            raise PreflightError('invalid_base')
        return resolved
    if (re.fullmatch(r'[0-9a-fA-F]+', token) or
            not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_./-]*', token)):
        raise PreflightError('invalid_base')
    ref = git(repo, 'rev-parse', '--symbolic-full-name', '--verify', '--end-of-options', token).strip()
    if not ref.startswith(('refs/heads/', 'refs/tags/', 'refs/remotes/')) or '\n' in ref:
        raise PreflightError('invalid_base')
    return git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').strip()


def main():
    data = dict(repo_path=None, local_head=None, expected_head=None, base_sha=None,
                merge_base=None, porcelain_status=None, changed_files=[], preflight='Error',
                runtime_suitable=False, safe_to_run_local_checks=False, blockers=[],
                runtime={'status': 'Not verified', 'reason': 'Manual runtime identity record required.'},
                review_approval='Not assessed', github={'status': 'Not requested'})
    try:
        parser = Parser(description=__doc__, allow_abbrev=False)
        parser.add_argument('--repo', required=True)
        parser.add_argument('--expected-head', required=True)
        parser.add_argument('--base', required=True)
        parser.add_argument('--expected-base')
        args = parser.parse_args()
        if not SHA.fullmatch(args.expected_head):
            raise PreflightError('invalid_expected_head')
        if args.expected_base is not None and not SHA.fullmatch(args.expected_base):
            raise PreflightError('invalid_expected_base')
        data['expected_base'] = args.expected_base
        data['base_identity'] = 'Not verified' if args.expected_base is None else 'Compared to supplied snapshot'
        data['expected_head'] = args.expected_head
        repo = Path(args.repo).resolve()
        data['repo_path'] = str(repo)
        head = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').strip()
        data['local_head'] = head
        base = resolve_base(repo, args.base)
        data['base_sha'] = base
        if args.expected_base is not None and base != args.expected_base:
            data['blockers'].append('base_mismatch')
        merge_base = git(repo, 'merge-base', base, head).strip()
        data['merge_base'] = merge_base
        status = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        data['porcelain_status'] = status
        files = git(repo, 'diff', '--no-ext-diff', '--name-only', '-z', '--no-renames', merge_base, head, '--')
        data['changed_files'] = files.split('\0')[:-1]
        if head != args.expected_head:
            data['blockers'].append('head_mismatch')
        if status:
            data['blockers'].append('dirty_worktree')
        data['preflight'] = 'Blocked' if data['blockers'] else 'Pass'
        data['safe_to_run_local_checks'] = not data['blockers']
        # A matching checkout cannot prove which server a browser is testing.
        data['runtime_suitable'] = False
        code = 1 if data['blockers'] else 0
    except PreflightError as exc:
        data['error_code'] = str(exc)
        code = 2
    except (OSError, ValueError, subprocess.SubprocessError):
        # Never emit child stderr, commands, environment or authentication details.
        data['error_code'] = 'command_or_repository_error'
        code = 2
    print(json.dumps(data, ensure_ascii=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
