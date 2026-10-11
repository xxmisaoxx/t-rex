#!/usr/bin/env python3
"""Ghidra discovery, isolated headless analysis and bounded evidence reads (stdlib only)."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
INSTALL_URL = 'https://github.com/NationalSecurityAgency/ghidra/releases'
KINDS = ('functions', 'strings', 'symbols', 'segments', 'details')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)


def project_fingerprint(directory, name):
    """Bind the private program database, excluding UI preferences and rotating index backups."""
    root = Path(directory) / (name + '.rep') / 'idata'
    files = sorted(p for p in root.rglob('*') if p.is_file() and
                   not p.name.endswith(('.bak', '.lock', '.tmp')))
    if not files:
        raise ValueError('Saved private program database is missing')
    h = hashlib.sha256()
    for p in files:
        h.update(p.relative_to(root).as_posix().encode('utf-8') + b'\0')
        h.update(bytes.fromhex(sha256(p)))
    return {'sha256': h.hexdigest(), 'files': len(files), 'scope': 'private project idata excluding .bak/.lock/.tmp'}


def properties(path):
    if not path.is_file():
        return {}
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip()
    return result


def find_ghidra(explicit=None):
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    elif os.environ.get('GHIDRA_HOME'):
        candidates.append(Path(os.environ['GHIDRA_HOME']).expanduser())
    else:
        located = shutil.which('analyzeHeadless') or shutil.which('analyzeHeadless.bat')
        if located:
            candidates.append(Path(located))
        roots = [Path.home(), Path.home() / 'tools', Path('/opt'), Path('/usr/local/share')]
        if os.name == 'nt':
            roots += [Path(os.environ.get('ProgramFiles', 'C:/Program Files')), Path('C:/tools')]
        for parent in roots:
            if parent.is_dir():
                candidates += sorted(parent.glob('ghidra*'), reverse=True)
    name = 'analyzeHeadless.bat' if os.name == 'nt' else 'analyzeHeadless'
    for path in candidates:
        launcher = path if path.is_file() else path / 'support' / name
        home = launcher.parent.parent
        if launcher.is_file() and (home / 'Ghidra/application.properties').is_file():
            return home.resolve(), launcher.resolve()
    return None, None


def doctor(ghidra_home=None, java_home=None):
    home, launcher = find_ghidra(ghidra_home)
    props = properties(home / 'Ghidra/application.properties') if home else {}
    launch_props = properties(home / 'support/launch.properties') if home else {}
    selected_java = launch_props.get('JAVA_HOME_OVERRIDE') or java_home or os.environ.get('JAVA_HOME')
    java = str(Path(selected_java) / 'bin' / ('java.exe' if os.name == 'nt' else 'java')) if selected_java else shutil.which('java')
    java_info = {'path': java, 'status': 'missing', 'major': None}
    if java:
        try:
            p = subprocess.run([java, '-version'], capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=10)
            output = p.stdout + p.stderr
            match = re.search(r'version\s+"(\d+)(?:\.(\d+))?', output)
            major = int(match[2]) if match and match[1] == '1' else int(match[1]) if match else None
            java_info.update(status='found' if p.returncode == 0 else 'failed', major=major,
                             version_output=output.strip()[:1000])
        except (OSError, subprocess.TimeoutExpired) as exc:
            java_info.update(status='failed', error=str(exc))
    javac = Path(java).resolve().parent / ('javac.exe' if os.name == 'nt' else 'javac') if java else None
    java_info['jdk_found'] = bool(javac and javac.is_file())
    minimum = launch_props.get('JAVA_MINIMUM_VERSION') or props.get('application.java.min')
    minimum = int(minimum.split('.')[0]) if minimum and minimum.split('.')[0].isdigit() else None
    compatible = bool(home and java_info['status'] == 'found' and java_info['jdk_found'] and
                      (minimum is None or (java_info['major'] or 0) >= minimum))
    return {'provider': 'ghidra', 'status': 'available' if compatible else 'unavailable',
            'ghidra_home': str(home) if home else None, 'launcher': str(launcher) if launcher else None,
            'version': props.get('application.version'), 'minimum_java': minimum,
            'java': java_info, 'java_home_override': launch_props.get('JAVA_HOME_OVERRIDE') or None,
            'launch_verified': False,
            'guidance': 'Download the official release ZIP (not Source Code), extract it, install the JDK required by that release, and set GHIDRA_HOME or pass --ghidra-home. Check that release\'s Getting Started guide; launcher overrides may choose another JDK.',
            'install_url': INSTALL_URL}


def windows_command(command):
    # cmd expands percent/exclamation even in quotes. Reject them rather than silently change paths.
    if any(any(c in str(a) for c in '%!^"\r\n') for a in command):
        raise ValueError('Windows launcher arguments cannot contain %, !, ^, quotes or newlines')
    # Pass the complete native command line. Popen's list2cmdline would add
    # backslash escapes to nested quotes, which cmd.exe does not interpret.
    return 'cmd.exe /d /s /c "' + ' '.join('"' + str(a) + '"' for a in command) + '"'


def run_process(command, output, timeout, java_home=None):
    env = os.environ.copy()
    if java_home:
        env['JAVA_HOME'] = str(Path(java_home).resolve())
        env['PATH'] = str(Path(java_home).resolve() / 'bin') + os.pathsep + env.get('PATH', '')
    command = windows_command(command) if os.name == 'nt' and str(command[0]).lower().endswith(('.bat', '.cmd')) else command
    with (output / 'headless.log').open('wb') as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, env=env,
                                start_new_session=os.name != 'nt')
        try:
            return proc.wait(timeout=timeout), False
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                finally:
                    if proc.poll() is None:
                        proc.kill()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait()
            return proc.returncode, True


def analyze(args, reuse=False):
    source = None
    if reuse:
        base = Path(args.analysis).resolve()
        source = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
        if source.get('schema_version') != '1.0' or source.get('provider', {}).get('name') != 'ghidra':
            raise ValueError('Expected a T-REX Ghidra evidence directory')
        if source['status'] not in ('success', 'partial'):
            raise ValueError('Cannot reuse a failed analysis')
        target = Path(source['artifact']['path'])
    else:
        target = Path(args.target).expanduser().resolve()
    if not target.is_file():
        raise ValueError('Target file not found: ' + str(target))
    artifact = {'path': str(target), 'size': target.stat().st_size, 'sha256': sha256(target)}
    if source and artifact != source['artifact']:
        raise ValueError('Target identity changed; create a new analysis for this revision')
    home_arg = args.ghidra_home or (source['provider']['home'] if source else None)
    found = doctor(home_arg, args.java_home)
    if found['status'] != 'available':
        return {'status': 'failed', 'error': 'Ghidra/JDK unavailable', 'doctor': found}
    if source and source['provider']['version'] != found['version']:
        raise ValueError('Ghidra version changed; create a new analysis instead of upgrading the cached project')
    if source and project_fingerprint(source['project']['directory'], source['project']['name']) != source['project'].get('fingerprint'):
        raise ValueError('Cached program database changed; create a new analysis for this project revision')
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    project_dir = Path(source['project']['directory']) if source else output / 'project'
    project_name = source['project']['name'] if source else 'trex_' + run_id
    if source and not (project_dir / (project_name + '.gpr')).is_file():
        raise ValueError('Cached project is missing; create a new analysis')
    project_dir.mkdir(parents=True, exist_ok=True)
    request = {'schema_version': '1.0', 'run_id': run_id, 'expected_sha256': artifact['sha256'],
               'inventory': not reuse, 'selectors': args.function,
               'max_items': args.max_items, 'max_functions': args.max_functions,
               'max_instructions': args.max_instructions, 'max_refs': args.max_refs,
               'max_text_chars': args.max_text_chars, 'max_pseudocode_chars': args.max_pseudocode_chars,
               'decompile_timeout': args.decompile_timeout}
    write_json(output / 'request.json', request)
    command = [found['launcher'], str(project_dir), project_name]
    if reuse:
        command += ['-process', source['project']['program'], '-noanalysis', '-readOnly']
    else:
        # Avoid option-like filenames and wildcards in the project program name.
        if target.name.startswith('-') or any(c in target.name for c in '*?'):
            raise ValueError('Use a target filename without leading - or wildcard characters')
        command += ['-import', str(target), '-analysisTimeoutPerFile', str(args.analysis_timeout)]
    command += ['-scriptPath', str(ROOT / 'scripts/ghidra'), '-postScript', 'TrexExport.java',
                str(output / 'request.json'), str(output), '-log', str(output / 'ghidra.log'),
                '-scriptlog', str(output / 'script.log')]
    manifest = {'schema_version': '1.0', 'run_id': run_id, 'status': 'running',
                'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'artifact': artifact,
                'provider': {'name': 'ghidra', 'version': found['version'], 'home': found['ghidra_home'],
                             'java': found['java'], 'exporter_sha256': sha256(ROOT / 'scripts/ghidra/TrexExport.java')},
                'project': {'directory': str(project_dir), 'name': project_name,
                            'program': source['project']['program'] if source else target.name},
                'operation': 'function' if reuse else 'analyze', 'command': command,
                'request': request, 'reused_analysis': str(base) if source else None,
                'coverage': 'unknown', 'files': {}}
    write_json(output / 'manifest.json', manifest)
    start = time.monotonic()
    try:
        code, timed_out = run_process(command, output, args.timeout, args.java_home)
        manifest.update(returncode=code, timed_out=timed_out)
        metadata_path = output / 'metadata.json'
        metadata = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.is_file() else None
        if timed_out or code != 0 or not metadata:
            manifest.update(status='failed', coverage='failed', error='Headless run did not complete; inspect headless.log and retained partial files')
        elif metadata.get('run_id') != run_id or metadata.get('program_sha256', '').lower() != artifact['sha256']:
            manifest.update(status='failed', coverage='failed', error='Exported project identity does not match this run/target')
        elif sha256(target) != artifact['sha256']:
            manifest.update(status='failed', coverage='failed', error='Target changed during analysis')
        else:
            manifest['metadata'] = metadata
            manifest['project']['program'] = metadata['program']
            fingerprint = project_fingerprint(project_dir, project_name)
            if source and fingerprint != source['project']['fingerprint']:
                raise ValueError('Cached program database changed during the query')
            manifest['project']['fingerprint'] = fingerprint
            if source and source.get('metadata', {}).get('analysis_timed_out'):
                metadata['analysis_timed_out'] = True
            partial = metadata['analysis_timed_out'] or any(
                c.get('coverage') != 'complete' for c in metadata['collections'].values())
            manifest.update(status='partial' if partial else 'success', coverage='partial' if partial else 'complete')
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        manifest.update(status='failed', coverage='failed', error=str(exc))
    manifest['duration_seconds'] = round(time.monotonic() - start, 3)
    for p in output.iterdir():
        if p.is_file() and p.name != 'manifest.json':
            manifest['files'][p.name] = {'size': p.stat().st_size, 'sha256': sha256(p)}
    write_json(output / 'manifest.json', manifest)
    return {'status': manifest['status'], 'coverage': manifest['coverage'], 'run_id': run_id,
            'output': str(output), 'manifest': str(output / 'manifest.json'),
            'error': manifest.get('error'), 'metadata': manifest.get('metadata')}


def view(args):
    base = Path(args.analysis).resolve()
    manifest = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
    name = args.kind + '.jsonl'
    path = base / name
    expected = manifest.get('files', {}).get(name)
    if not expected or not path.is_file() or sha256(path) != expected['sha256']:
        raise ValueError('Evidence file missing or changed: ' + name)
    rows, matches = [], 0
    with path.open(encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            if args.contains and args.contains.casefold() not in line.casefold():
                continue
            if args.offset <= matches < args.offset + args.limit:
                rows.append(row)
            matches += 1
    coverage = manifest.get('metadata', {}).get('collections', {}).get(args.kind, {})
    return {'run_id': manifest['run_id'], 'artifact': manifest['artifact'], 'kind': args.kind,
            'source': name, 'source_sha256': expected['sha256'], 'collection': coverage,
            'offset': args.offset, 'matches_in_export': matches, 'rows': rows,
            'next_offset': args.offset + len(rows) if args.offset + len(rows) < matches else None}


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('Must be positive')
    return number


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    d = sub.add_parser('doctor', help='Locate Ghidra and Java; print installation guidance')
    for cmd in [d, sub.add_parser('analyze', help='Import and analyze a binary'),
                sub.add_parser('function', help='Read functions from a saved project without reanalysis')]:
        cmd.add_argument('--ghidra-home')
        cmd.add_argument('--java-home')
        if cmd is d:
            continue
        if cmd.prog.endswith(' analyze'):
            cmd.add_argument('target')
        else:
            cmd.add_argument('--analysis', required=True)
        cmd.add_argument('--output', required=True, help='New evidence directory; never overwrites a previous run')
        cmd.add_argument('--function', action='append', default=[], help='Exact function name or absolute 0x address; repeat for multiple functions')
        cmd.add_argument('--max-items', type=positive, default=5000)
        cmd.add_argument('--max-functions', type=positive, default=10)
        cmd.add_argument('--max-instructions', type=positive, default=2000)
        cmd.add_argument('--max-refs', type=positive, default=1000)
        cmd.add_argument('--max-text-chars', type=positive, default=4096)
        cmd.add_argument('--max-pseudocode-chars', type=positive, default=100000)
        cmd.add_argument('--decompile-timeout', type=positive, default=30)
        cmd.add_argument('--analysis-timeout', type=positive, default=300)
        cmd.add_argument('--timeout', type=positive, default=900, help='Whole process timeout in seconds')
    v = sub.add_parser('view', help='Read a verified, filtered page of exported inventory')
    v.add_argument('--analysis', required=True)
    v.add_argument('--kind', choices=KINDS, required=True)
    v.add_argument('--contains')
    v.add_argument('--offset', type=int, default=0)
    v.add_argument('--limit', type=positive, default=50)
    args = p.parse_args(argv)
    try:
        if args.action == 'doctor':
            result = doctor(args.ghidra_home, args.java_home)
        elif args.action == 'view':
            if args.offset < 0:
                raise ValueError('Offset cannot be negative')
            result = view(args)
        else:
            if args.action == 'function' and not args.function:
                raise ValueError('Specify at least one --function name/address')
            result = analyze(args, args.action == 'function')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get('status') in ('failed', 'unavailable') else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
