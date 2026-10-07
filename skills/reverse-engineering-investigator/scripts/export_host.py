#!/usr/bin/env python3
"""Export one verified skill tree into a fresh staging layout; never install it."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('invalid relative package/layout path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('unsafe relative package/layout path')
    return Path(*path.parts)


def export(host, out, scope='project', source=ROOT):
    source = Path(source).resolve()
    registry = json.loads((source / 'hosts/registry.json').read_text(encoding='utf-8'))
    if host not in registry['hosts']:
        raise ValueError('unknown host: ' + host)
    if scope not in ('project', 'user'):
        raise ValueError('scope must be project or user')
    selected = registry['hosts'][host]
    layout = selected[scope]
    if layout is None:
        raise ValueError('this host has no documented user-scope export')
    destination = relative_path(layout) / relative_path(registry['skill_name'])
    manifest = json.loads((source / 'MANIFEST.json').read_text(encoding='utf-8'))
    files = [relative_path(name) for name in manifest['files']]
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*')
              if p.is_file() and p.name != 'MANIFEST.json' and '__pycache__' not in p.parts}
    if actual != set(manifest['files']):
        raise ValueError('source manifest inventory mismatch')
    for name in files + [Path('MANIFEST.json')]:
        path = source / name
        if any(part.is_symlink() for part in [path, *path.parents] if part != source and source in part.parents):
            raise ValueError('symlinked package member: ' + str(name))
        if not path.is_file():
            raise ValueError('missing package member: ' + str(name))
        if name.as_posix() in manifest['files']:
            content = path.read_bytes()
            expected = manifest['files'][name.as_posix()]
            if len(content) != expected['size'] or hashlib.sha256(content).hexdigest() != expected['sha256']:
                raise ValueError('source manifest byte mismatch: ' + str(name))
    requested = Path(out).expanduser()
    if requested.exists() or requested.is_symlink():
        raise ValueError('output already exists; choose a fresh staging directory')
    out = requested.resolve()
    if out == source or source in out.parents or out in source.parents:
        raise ValueError('staging output overlaps the source package')
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.re-export-', dir=out.parent))
    try:
        target = stage / destination
        target.mkdir(parents=True)
        for name in files + [Path('MANIFEST.json')]:
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, dest)
        pointer = destination.as_posix() + '/SKILL.md'
        if scope == 'user':
            pointer = '~/' + pointer
        loader = (
            '# Optional reverse-engineering loader fragment\n\n'
            'For a reverse-engineering task, read `' + pointer + '` and follow its workflow. '
            'Resolve bundled resources from that skill directory and investigation state from its project directory. '
            'Recover existing canonical state before new discovery; load only the relevant profile and host adapter.\n\n'
            'Merge this text only into an instruction mechanism your host actually reads. '
            'This fragment is not automatically loaded and does not replace existing project instructions.\n'
        )
        (stage / 'LOADER.fragment.md').write_text(loader, encoding='utf-8')
        receipt = {'host': host, 'scope': scope, 'release_version': manifest['version'],
                   'skill_path': destination.as_posix(), 'source_manifest_sha256':
                   hashlib.sha256((source / 'MANIFEST.json').read_bytes()).hexdigest(),
                   'files_copied': len(files) + 1, 'installed': False,
                   'invocation': selected['invocation'], 'documentation_checked': registry['verified_on']}
        (stage / 'EXPORT.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        # mkdir is exclusive, including against a concurrent exporter. Only this
        # newly created directory is cleaned up on a failed final copy.
        out.mkdir()
        try:
            for child in stage.iterdir():
                shutil.move(str(child), str(out / child.name))
        except Exception:
            shutil.rmtree(out)
            raise
        return receipt
    finally:
        shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=sorted(json.loads((ROOT / 'hosts/registry.json').read_text())['hosts']))
    parser.add_argument('--scope', choices=['project', 'user'], default='project',
                        help='layout only: output represents a project root or home root')
    parser.add_argument('--out', required=True, help='fresh staging directory, not an existing project/home')
    args = parser.parse_args()
    try:
        print(json.dumps(export(args.host, args.out, args.scope), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'Export failed: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
