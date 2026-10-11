#!/usr/bin/env python3
"""Direct Rizin CLI provider; Cutter is detected separately as a GUI."""
import datetime as dt
import json
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid

from re_tools import sha256, write_json

RELEASES = 'https://github.com/rizinorg/rizin/releases'


def quote_path(path):
    text = str(path)
    if any(c in text for c in '\r\n\0`$"'):
        raise ValueError('Rizin project path contains unsupported command syntax characters')
    return json.dumps(text, ensure_ascii=False)


def find_rizin(explicit=None):
    name = 'rizin.exe' if os.name == 'nt' else 'rizin'
    supplied = explicit or os.environ.get('RIZIN_PATH') or os.environ.get('RIZIN_HOME')
    if supplied:
        p = Path(supplied).expanduser()
        candidates = [p] if p.is_file() else [p / name, p / 'bin' / name]
    else:
        candidates = [Path(p) for p in [shutil.which(name)] if p]
        roots = [Path.home() / 'tools', Path('/opt'), Path('/usr/local'), Path('C:/tools')]
        for root in roots:
            if root.is_dir():
                for p in sorted(root.glob('rizin*')) + sorted(root.glob('Cutter*')):
                    candidates += [p / name, p / 'bin' / name, p / 'Contents/MacOS' / name]
    return next((p.resolve() for p in candidates if p.is_file()), None)


def doctor(explicit=None):
    path = find_rizin(explicit)
    result = {'provider': 'rizin', 'status': 'unavailable', 'path': str(path) if path else None,
              'version': None, 'launch_verified': False, 'install_url': RELEASES,
              'guidance': 'Install an official Rizin CLI release; set RIZIN_PATH to its executable or pass --rizin-path. Cutter alone does not guarantee an exposed CLI or a decompiler plugin.'}
    if path:
        try:
            p = subprocess.run([str(path), '-v'], capture_output=True, timeout=10,
                               stdin=subprocess.DEVNULL, encoding='utf-8', errors='replace')
            text = p.stdout + p.stderr
            match = re.search(r'\brizin\s+(\d+\.\d+\.\d+)', text)
            if p.returncode == 0 and match:
                result.update(status='available', version=match[1], launch_verified=True,
                              executable_sha256=sha256(path))
            else:
                result['error'] = text[:1000]
        except (OSError, subprocess.SubprocessError) as exc:
            result['error'] = str(exc)
    return result


def inventory():
    """Shallow GUI discovery; no claims about edition, API or plugin availability."""
    found = []
    websites = {'cutter': 'https://github.com/rizinorg/cutter/releases', 'ida': 'https://hex-rays.com/',
                'binary-ninja': 'https://binary.ninja/', 'x64dbg': 'https://x64dbg.com/',
                'imhex': 'https://github.com/WerWolv/ImHex/releases'}
    for tool, names in {'cutter': ['cutter', 'Cutter.exe'], 'ida': ['ida', 'ida64', 'ida.exe'],
                        'binary-ninja': ['binaryninja', 'binaryninja.exe'],
                        'x64dbg': ['x64dbg.exe', 'x32dbg.exe'], 'imhex': ['imhex', 'imhex.exe']}.items():
        paths = [Path(p) for name in names if (p := shutil.which(name))]
        env = os.environ.get(tool.upper().replace('-', '_') + '_HOME')
        if env:
            paths += [Path(env) / n for n in names] + [Path(env) / 'bin' / n for n in names]
        roots = [Path('/Applications'), Path('/opt'), Path.home() / 'tools']
        if os.name == 'nt':
            roots += [Path(os.environ.get('ProgramFiles', 'C:/Program Files')), Path('C:/tools')]
        for root in roots:
            if root.is_dir():
                for directory in root.glob('*'):
                    if tool.replace('-', '') in directory.name.lower().replace(' ', '').replace('-', ''):
                        paths += [directory / n for n in names] + [directory / 'bin' / n for n in names]
                        paths += [directory / 'Contents/MacOS' / n for n in names]
        paths = sorted({str(p.resolve()) for p in paths if p.is_file()})
        found.append({'tool': tool, 'status': 'detected' if paths else 'not_detected',
                      'paths': paths, 'integration': 'GUI/host capability; no bundled executable adapter',
                      'install_url': websites[tool],
                      'guidance': 'Check this official distribution and your edition/API if needed; not_detected is a bounded search result, not proof of absence.',
                      'edition_and_api': 'not_verified', 'search_scope': 'PATH, optional TOOL_HOME, shallow common directories'})
    return found


class RizinPipe:
    def __init__(self, executable, target, output, timeout, cancel_event=None):
        self.deadline = time.monotonic() + timeout
        self.cancel_event = cancel_event
        self.frames = queue.Queue()
        self.stderr = (output / 'headless.log').open('wb')
        self.command = [str(executable), '-N', '-q0', '-e', 'scr.color=0', '-e', 'scr.interactive=false', str(target)]
        self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.stderr, start_new_session=os.name != 'nt')
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self._frame()
        except BaseException:
            self.close()
            raise

    def _read(self):
        data = bytearray()
        try:
            while chunk := os.read(self.proc.stdout.fileno(), 65536):
                for part in chunk.split(b'\0')[:-1]:
                    data.extend(part)
                    if len(data) > 16 * 1024 * 1024:
                        raise ValueError('Rizin response exceeded 16 MiB; retained earlier slices only')
                    self.frames.put(bytes(data)); data.clear()
                data.extend(chunk.rsplit(b'\0', 1)[-1])
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError('Rizin response exceeded 16 MiB; retained earlier slices only')
            self.frames.put(EOFError('Rizin exited before a complete response'))
        except (OSError, ValueError) as exc:
            self.frames.put(exc)

    def _frame(self, timeout=None):
        deadline = min(self.deadline, time.monotonic() + timeout) if timeout else self.deadline
        while True:
            if self.cancel_event and self.cancel_event.is_set():
                raise InterruptedError('Analysis cancelled')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Rizin operation timeout')
            try:
                frame = self.frames.get(timeout=min(remaining, 0.1))
                if isinstance(frame, Exception):
                    raise frame
                return frame.decode('utf-8', errors='replace').strip()
            except queue.Empty:
                pass

    def cmd(self, command, timeout=None):
        self.proc.stdin.write((command + '\n').encode('utf-8')); self.proc.stdin.flush()
        return self._frame(timeout)

    def close(self):
        if self.proc.poll() is None:
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill', '/PID', str(self.proc.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                except subprocess.SubprocessError:
                    pass
            else:
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if self.proc.poll() is None:
                self.proc.kill()
        self.proc.wait(); self.reader.join(timeout=2)
        self.proc.stdin.close(); self.proc.stdout.close(); self.stderr.close()


def analyze(args, reuse=False):
    source = None
    if reuse:
        base = Path(args.analysis).resolve()
        source = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
        if source.get('schema_version') != '1.0' or source.get('provider', {}).get('name') != 'rizin':
            raise ValueError('Expected a T-REX Rizin analysis')
        if source['status'] not in ('success', 'partial'):
            raise ValueError('Cannot reuse failed analysis')
        target = Path(source['artifact']['path'])
        project = Path(source['project']['path'])
        if not project.is_file() or sha256(project) != source['project']['sha256']:
            raise ValueError('Cached project missing or changed; create a new analysis')
    else:
        target = Path(args.target).expanduser().resolve()
    if not target.is_file():
        raise ValueError('Target file not found')
    artifact = {'path': str(target), 'size': target.stat().st_size, 'sha256': sha256(target)}
    if source and source['artifact'] != artifact:
        raise ValueError('Target identity changed; create a new analysis')
    supplied = getattr(args, 'rizin_path', None) or (source['provider']['path'] if source else None)
    provider = doctor(supplied)
    if provider['status'] != 'available':
        return {'status': 'failed', 'error': 'Rizin unavailable', 'doctor': provider}
    if source and (provider['version'] != source['provider']['version'] or
                   provider['executable_sha256'] != source['provider']['executable_sha256']):
        raise ValueError('Rizin executable changed; create a new analysis')
    output = Path(args.output).expanduser().resolve(); output.mkdir(parents=True, exist_ok=False)
    (output / 'raw').mkdir()
    if not reuse:
        project = output / 'project.rzdb'
    run_id = uuid.uuid4().hex
    manifest = {'schema_version': '1.0', 'run_id': run_id, 'status': 'running', 'coverage': 'unknown',
                'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'artifact': artifact,
                'provider': {'name': 'rizin', 'version': provider['version'], 'path': provider['path'],
                             'executable_sha256': provider['executable_sha256'], 'exporter_sha256': sha256(__file__)},
                'operation': 'function' if reuse else 'analyze', 'files': {},
                'reused_analysis': str(base) if reuse else None,
                'request': {k: getattr(args, k) for k in ('function', 'max_items', 'max_functions', 'max_instructions',
                           'max_refs', 'max_text_chars', 'max_pseudocode_chars', 'timeout', 'analysis_timeout', 'decompile_timeout')}}
    write_json(output / 'request.json', manifest['request']); write_json(output / 'manifest.json', manifest)
    collections = {}; serial = 0; pipe = None
    def command(cmd, label, json_result=True, timeout=None):
        nonlocal serial
        serial += 1
        text = pipe.cmd(cmd, timeout)
        name = 'raw/%04d-%s.txt' % (serial, label)
        (output / name).write_text(text, encoding='utf-8')
        with (output / 'commands.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'command': cmd, 'raw': name, 'sha256': sha256(output / name)}) + '\n')
        return json.loads(text) if json_result else text
    def row(kind, address, suffix=''):
        value = {'evidence_id': run_id + ':' + kind + ':' + str(address) + suffix,
                 'address': hex(address) if isinstance(address, int) else None, 'address_space': 'analysis_va'}
        if isinstance(address, int) and address >= image_base:
            value['rva'] = hex(address - image_base)
        return value
    def emit(kind, records, total=None, complete=True):
        with (output / (kind + '.jsonl')).open('x', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        count = len(records); total = count if total is None else total
        collections[kind] = {'exported': count, 'total_in_database': total,
                             'coverage': 'complete' if complete and count == total else 'partial'}
    start = time.monotonic()
    try:
        pipe = RizinPipe(provider['path'], target, output, args.timeout, getattr(args, 'cancel_event', None))
        manifest['command'] = pipe.command
        if reuse:
            # Copy on read: never expose the original project to a save operation.
            local_project = output / 'project-input.rzdb'; shutil.copyfile(project, local_project)
            command('Poo ' + quote_path(local_project), 'open-project', False)
        else:
            command('aaa', 'analysis', False, args.analysis_timeout)
        info = command('ij', 'info')
        if Path(info['core']['file']).resolve() != target.resolve() or info['core'].get('iorw'):
            raise ValueError('Loaded program identity or read-only mode mismatch')
        binary = info.get('bin', {}); image_base = binary.get('baddr', 0)
        functions = command('aflj', 'functions')
        sections = command('iSj', 'sections')
        refs = command('axlj', 'xrefs')
        if not all(isinstance(x, list) for x in (functions, sections, refs)):
            raise ValueError('Unexpected Rizin JSON collection shape')
        def function_row(f):
            o = row('function', f['offset']); o.update(name=f['name'], signature=f.get('signature'), body_size=f.get('size'))
            return o
        if not reuse:
            emit('functions', [function_row(f) for f in functions[:args.max_items]], len(functions))
            strings = command('izj', 'strings'); symbols = command('isj', 'symbols')
            string_rows = []
            for s in strings[:args.max_items]:
                o = row('string', s.get('vaddr')); text = s.get('string', '')
                o.update(value=text[:args.max_text_chars], value_truncated=len(text) > args.max_text_chars,
                         value_length_chars=len(text), length_bytes=s.get('size'), file_offset=s.get('paddr'))
                string_rows.append(o)
            emit('strings', string_rows, len(strings), all(not s['value_truncated'] for s in string_rows))
            symbol_rows = []
            for i, s in enumerate(symbols[:args.max_items]):
                o = row('symbol', s.get('vaddr'), ':' + str(i)); o.update(name=s.get('name'), type=s.get('type'), imported=s.get('is_imported'), file_offset=s.get('paddr'))
                symbol_rows.append(o)
            emit('symbols', symbol_rows, len(symbols))
            segment_rows = []
            for i, s in enumerate(sections[:args.max_items]):
                o = row('segment', s.get('vaddr'), ':' + str(i)); o.update(name=s.get('name'), size=s.get('vsize'), file_size=s.get('size'), file_offset=s.get('paddr'), permissions=s.get('perm'), scope='binary section')
                segment_rows.append(o)
            emit('segments', segment_rows, len(sections))
        plugin = command('pdg?', 'decompiler-probe', False)
        decompiler = bool(re.search(r'\bpdg\b', plugin))
        selected = []; unresolved = []
        if args.function:
            for selector in args.function:
                matches = [f for f in functions if f['name'] == selector or
                           (re.fullmatch(r'0x[0-9a-fA-F]+', selector) and f['offset'] == int(selector, 16))]
                if not matches:
                    unresolved.append(selector)
                for f in matches:
                    if f not in selected:
                        selected.append(f)
        else:
            selected = functions[:args.max_functions]
        details = []
        with target.open('rb') as target_bytes:
            for f in selected[:args.max_functions]:
                addr = hex(f['offset']); detail = function_row(f)
                body = command('pdfj @ ' + addr, 'body')
                ops = body.get('ops', [])
                instructions = []
                for op in ops[:args.max_instructions]:
                    i = row('instruction', op['offset']); i.update(text=op.get('disasm', op.get('opcode')), bytes=op.get('bytes'))
                    i['byte_verification'] = 'unmapped'
                    raw = bytes.fromhex(i['bytes'] or '')
                    for section in sections:
                        va = section.get('vaddr', 0); offset = section.get('paddr')
                        if offset is not None and raw and va <= op['offset'] and op['offset'] + len(raw) <= va + section.get('size', 0):
                            i['file_offset'] = offset + op['offset'] - va
                            target_bytes.seek(i['file_offset'])
                            i['byte_verification'] = 'match' if target_bytes.read(len(raw)) == raw else 'mismatch'
                            break
                    instructions.append(i)
                addresses = {op['offset'] for op in ops}
                incoming = [r for r in refs if r.get('to') == f['offset']]
                outgoing = [r for r in refs if r.get('from') in addresses]
                def reference(r):
                    o = row('reference', r['from'], ':' + str(r['to']) + ':' + r.get('type', ''))
                    o.update(from_address=hex(r['from']), to_address=hex(r['to']), type=r.get('type'))
                    return o
                detail.update(instructions=instructions, instruction_count=len(ops),
                              instructions_coverage='complete' if len(instructions) == len(ops) else 'partial',
                              incoming_references=[reference(r) for r in incoming[:args.max_refs]], incoming_count=len(incoming),
                              incoming_scope='function entry only', outgoing_references=[reference(r) for r in outgoing[:args.max_refs]],
                              outgoing_count=len(outgoing), references_coverage='complete' if max(len(incoming), len(outgoing)) <= args.max_refs else 'partial',
                              decompile_status='unavailable', decompile_error='rz-ghidra plugin not detected', pseudocode_truncated=False)
                if decompiler:
                    code = command('pdg @ ' + addr, 'pseudocode', False, args.decompile_timeout)
                    detail.update(decompile_status='success' if code else 'failed', decompile_error=None if code else 'Empty plugin output',
                                  pseudocode=code[:args.max_pseudocode_chars], pseudocode_length_chars=len(code),
                                  pseudocode_truncated=len(code) > args.max_pseudocode_chars)
                detail['coverage'] = 'complete' if detail['instructions_coverage'] == detail['references_coverage'] == 'complete' and all(i['byte_verification'] == 'match' for i in instructions) and detail['decompile_status'] == 'success' and not detail['pseudocode_truncated'] else 'partial'
                details.append(detail)
        emit('details', details, len(selected), not unresolved and all(d['coverage'] == 'complete' for d in details))
        collections['details'].update(unresolved_selectors=unresolved, scope='requested functions' if args.function else 'sample of database')
        if not reuse:
            command('Ps ' + quote_path(project), 'save-project', False)
        if not project.is_file() or (source and sha256(project) != source['project']['sha256']):
            raise ValueError('Project was not saved or original project changed')
        if sha256(target) != artifact['sha256']:
            raise ValueError('Target changed during analysis')
        manifest['project'] = {'path': str(project), 'sha256': sha256(project)}
        metadata = {'schema_version': '1.0', 'run_id': run_id, 'program_sha256': artifact['sha256'],
                    'program': target.name, 'format': info['core'].get('format'), 'image_base': hex(image_base),
                    'language': '%s:%s:%s' % (binary.get('arch'), binary.get('bits'), binary.get('endian')),
                    'analysis_timed_out': False, 'collections': collections,
                    'capabilities': {'disassembly': True, 'decompilation': decompiler},
                    'coverage_meaning': 'Export coverage of Rizin database/requested slices; not exhaustive program recovery'}
        write_json(output / 'metadata.json', metadata); manifest['metadata'] = metadata
        partial = any(c['coverage'] != 'complete' for c in collections.values())
        manifest.update(status='partial' if partial else 'success', coverage='partial' if partial else 'complete')
    except (OSError, ValueError, KeyError, TypeError, EOFError, TimeoutError) as exc:
        manifest.update(status='failed', coverage='failed', error=str(exc), retained_collections=collections)
    finally:
        if pipe:
            pipe.close()
        manifest['duration_seconds'] = round(time.monotonic() - start, 3)
        for file in output.rglob('*'):
            if file.is_file() and file.name != 'manifest.json':
                manifest['files'][file.relative_to(output).as_posix()] = {'size': file.stat().st_size, 'sha256': sha256(file)}
        write_json(output / 'manifest.json', manifest)
    return {'status': manifest['status'], 'coverage': manifest['coverage'], 'run_id': run_id,
            'output': str(output), 'manifest': str(output / 'manifest.json'),
            'error': manifest.get('error'), 'metadata': manifest.get('metadata')}
