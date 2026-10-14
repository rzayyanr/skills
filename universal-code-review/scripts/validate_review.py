"""Validate review metadata consistency, never evidence truth or authorization."""
import argparse
import hashlib
from datetime import datetime
import json
import math
from pathlib import Path
import re

STATUSES = ('Pass', 'Fail', 'Not verified', 'Blocked', 'Not applicable', 'Not run', 'Not available')
RECORD = {'id': 'text', 'mandatory': 'bool', 'status': STATUSES,
          'method': ('Static', 'Automated', 'Runtime', 'Visual', 'Human'),
          'expected': 'text', 'actual': 'text', 'revision': 'sha', 'evidence_refs': ['text']}
SCHEMA = {
    'schema_version': 'version', 'target': {'head_sha': 'sha', 'base_sha': 'sha',
                                             'tested_merge_sha': 'sha_or_null'},
    'reviewed_at': 'datetime',
    'mode': ('Intake', 'Full Review', 'Re-review', 'Audit'),
    'recommendation': ('Approve', 'Request changes', 'Pending verification', 'Comment only'),
    'collection': {'complete': 'bool', 'items': [
        {'id': 'text', 'name': 'text', 'complete': 'bool',
         'expected_count': 'count', 'collected_count': 'count'}]},
    'requirements': [RECORD], 'checks': [RECORD], 'evidence': [
        {'id': 'text', 'kind': ('Static', 'Automated', 'Runtime', 'Visual', 'Human'),
         'revision': 'sha', 'base_sha': 'sha', 'location': 'text',
         'sha256': 'sha256', 'captured_at': 'datetime', 'summary': 'text'}],
    'findings': [{'id': 'text', 'severity': ('Blocker', 'Major', 'Minor', 'Informational'),
                  'origin': ('Introduced', 'Regression', 'Pre-existing', 'Uncertain'),
                  'status': ('Open', 'Resolved'), 'revision': 'sha',
                  'description': 'text', 'evidence_refs': ['text']}],
    'exceptions': [{'id': 'text', 'owner': 'text', 'rationale': 'text',
                    'scope': 'text', 'residual_risk': 'text',
                    'record_ids': ['text'], 'approved_at': 'datetime'}],
}


def check_shape(value, schema, path, errors):
    if isinstance(schema, dict):
        if type(value) is not dict:
            errors.append(f'{path}: expected object')
            return
        for key in value.keys() - schema.keys() - {'extensions'}:
            errors.append(f'{path}.{key}: unknown field (use extensions)')
        if 'extensions' in value and type(value['extensions']) is not dict:
            errors.append(f'{path}.extensions: expected object')
        for key, child in schema.items():
            if key not in value:
                errors.append(f'{path}.{key}: required field missing')
            else:
                check_shape(value[key], child, f'{path}.{key}', errors)
    elif isinstance(schema, list):
        if type(value) is not list:
            errors.append(f'{path}: expected array')
        else:
            for index, child in enumerate(value):
                check_shape(child, schema[0], f'{path}[{index}]', errors)
    elif isinstance(schema, tuple):
        if type(value) is not str or value not in schema:
            errors.append(f'{path}: expected one of {schema}')
    else:
        valid = {
            'text': lambda: type(value) is str and bool(value.strip()),
            'bool': lambda: type(value) is bool,
            'count': lambda: type(value) is int and value >= 0,
            'version': lambda: type(value) is int and value == 1,
            'sha': lambda: type(value) is str and re.fullmatch(r'[0-9a-fA-F]{40}', value) is not None,
            'sha_or_null': lambda: value is None or (type(value) is str and re.fullmatch(r'[0-9a-fA-F]{40}', value) is not None),
            'sha256': lambda: type(value) is str and re.fullmatch(r'[0-9a-fA-F]{64}', value) is not None,
            'datetime': lambda: type(value) is str and valid_datetime(value),
        }[schema]()
        if not valid:
            errors.append(f'{path}: invalid {schema}')


def valid_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
        return 'T' in value and parsed.tzinfo is not None and parsed.utcoffset() is not None
    except ValueError:
        return False


def check_artifact(artifact, root, errors):
    name = artifact['location']
    if ('\\' in name or ':' in name or name.startswith('/') or
            any(part in ('', '.', '..') for part in name.split('/'))):
        errors.append(f"{artifact['id']}: unsafe artifact path")
        return
    candidate = root.joinpath(*name.split('/'))
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root) or not candidate.is_file() or any(
            part.is_symlink() for part in (candidate, *candidate.parents) if part != root
        ):
            errors.append(f"{artifact['id']}: missing or unsafe artifact")
            return
        digest = hashlib.sha256()
        with candidate.open('rb') as handle:
            signature = handle.read(12)
            if artifact['kind'] == 'Visual':
                is_image = (
                    (candidate.suffix.lower() == '.png' and signature.startswith(b'\x89PNG\r\n\x1a\n')) or
                    (candidate.suffix.lower() in ('.jpg', '.jpeg') and signature.startswith(b'\xff\xd8\xff')) or
                    (candidate.suffix.lower() == '.webp' and signature[:4] == b'RIFF' and signature[8:12] == b'WEBP')
                )
                if not is_image:
                    errors.append(f"{artifact['id']}: Visual evidence needs an image artifact")
            handle.seek(0)
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != artifact['sha256'].lower():
            errors.append(f"{artifact['id']}: artifact checksum mismatch")
    except (OSError, ValueError):
        errors.append(f"{artifact['id']}: missing or unreadable artifact")


def validate(document, root):
    errors = []
    check_shape(document, SCHEMA, '$', errors)
    if errors:
        return errors
    rows = document['requirements'] + document['checks']
    objects = rows + document['evidence'] + document['collection']['items'] + document['findings'] + document['exceptions']
    seen = set()
    for item in objects:
        if item['id'] in seen:
            errors.append(f"{item['id']}: duplicate ID")
        seen.add(item['id'])
    evidence = {item['id']: item for item in document['evidence']}
    for artifact in document['evidence']:
        check_artifact(artifact, root, errors)
        if datetime.fromisoformat(artifact['captured_at']) > datetime.fromisoformat(document['reviewed_at']):
            errors.append(f"{artifact['id']}: evidence was captured after review timestamp")
    for row in rows:
        refs = row['evidence_refs']
        if len(refs) != len(set(refs)):
            errors.append(f"{row['id']}: duplicate evidence reference")
        for ref in refs:
            if ref not in evidence:
                errors.append(f"{row['id']}: unknown evidence reference {ref}")
        if row['status'] != 'Pass':
            continue
        if not refs:
            errors.append(f"{row['id']}: Pass requires evidence")
        if row['mandatory'] and row['revision'].lower() not in {
                document['target']['head_sha'].lower(),
                (document['target']['tested_merge_sha'] or '').lower()}:
            errors.append(f"{row['id']}: mandatory Pass revision differs from target head or declared merge result")
        for ref in refs:
            artifact = evidence.get(ref)
            if artifact is None:
                continue
            if artifact['revision'].lower() != row['revision'].lower():
                errors.append(f"{row['id']}: evidence {ref} revision differs from record")
            if artifact['kind'] != row['method']:
                errors.append(f"{row['id']}: evidence {ref} kind cannot certify {row['method']} method")
            if row['mandatory'] and artifact['base_sha'] != document['target']['base_sha']:
                errors.append(f"{row['id']}: mandatory evidence {ref} has stale base")
    for item in document['collection']['items']:
        if item['complete'] != (item['expected_count'] == item['collected_count']):
            errors.append(f"{item['id']}: completion contradicts collected count")
    items_complete = bool(document['collection']['items']) and all(
        item['complete'] for item in document['collection']['items'])
    if document['collection']['complete'] and not items_complete:
        errors.append('collection: marked complete with incomplete or missing items')

    for finding in document['findings']:
        if finding['revision'].lower() != document['target']['head_sha'].lower():
            errors.append(f"{finding['id']}: finding revision differs from target")
        for ref in finding['evidence_refs']:
            if ref not in evidence:
                errors.append(f"{finding['id']}: unknown evidence reference {ref}")
    row_ids = {row['id'] for row in rows}
    for exception in document['exceptions']:
        if not exception['record_ids']:
            errors.append(f"{exception['id']}: exception needs record IDs")
        for record_id in exception['record_ids']:
            if record_id not in row_ids:
                errors.append(f"{exception['id']}: unknown record ID {record_id}")

    decision = document['recommendation']
    if decision == 'Approve':
        if not document['collection']['complete'] or not items_complete:
            errors.append('Approve requires complete collection')
        if not document['requirements'] or not document['checks']:
            errors.append('Approve requires requirements and checks')
        for row in rows:
            if row['mandatory'] and row['status'] != 'Pass':
                errors.append(f"{row['id']}: mandatory item must Pass for Approve")
        for finding in document['findings']:
            if finding['status'] == 'Open' and finding['severity'] in ('Blocker', 'Major'):
                errors.append(f"{finding['id']}: unresolved major finding forbids Approve")
    elif decision == 'Request changes':
        if not (any(row['mandatory'] and row['status'] in ('Fail', 'Blocked') for row in rows)
                or any(f['status'] == 'Open' and f['severity'] in ('Blocker', 'Major')
                       for f in document['findings'])):
            errors.append('Request changes needs a failed required item or unresolved major finding')
    elif decision == 'Pending verification':
        if any(row['mandatory'] and row['status'] in ('Fail', 'Blocked') for row in rows):
            errors.append('Pending verification contradicts a failed mandatory item')
        if any(f['status'] == 'Open' and f['severity'] in ('Blocker', 'Major')
               for f in document['findings']):
            errors.append('Pending verification contradicts unresolved major finding')
    return errors


class InputParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('non-finite JSON number')
    return value


def reject_constant(text):
    raise ValueError(f'non-standard JSON constant: {text}')


def main():
    parser = InputParser(description=__doc__)
    parser.add_argument('--file', required=True)
    try:
        args = parser.parse_args()
        document = json.loads(Path(args.file).read_text(encoding='utf-8'),
                              object_pairs_hook=unique_object,
                              parse_float=finite_float, parse_constant=reject_constant)
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({'valid': False, 'evidence_verified': False,
                          'errors': [f'bad input: {exc}']}))
        return 2
    errors = validate(document, Path(args.file).resolve().parent)
    print(json.dumps({'valid': not errors, 'evidence_verified': False, 'errors': errors}))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
