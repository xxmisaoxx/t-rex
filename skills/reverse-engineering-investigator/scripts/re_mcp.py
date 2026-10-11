#!/usr/bin/env python3
"""Local stdio MCP interface with durable jobs over the CLI evidence adapters."""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import json
from functools import wraps
from pathlib import Path
import threading
import signal
from types import SimpleNamespace
from typing import Any
import uuid

import re_tools

DEFAULTS = {'max_items': 5000, 'max_functions': 10, 'max_instructions': 2000,
            'max_refs': 1000, 'max_text_chars': 4096, 'max_pseudocode_chars': 100000,
            'decompile_timeout': 30, 'analysis_timeout': 300, 'timeout': 900}
MAXIMUMS = {'max_items': 100000, 'max_functions': 100, 'max_instructions': 100000,
            'max_refs': 100000, 'max_text_chars': 100000, 'max_pseudocode_chars': 1000000,
            'decompile_timeout': 300, 'analysis_timeout': 3600, 'timeout': 14400}


class Jobs:
    def __init__(self, workspace, ghidra_home=None, java_home=None, rizin_path=None):
        self.root = Path(workspace).expanduser().resolve()
        if not self.root.is_dir():
            raise ValueError('Workspace must be an existing directory')
        self.directory = self.root / '.trex-jobs'; self.directory.mkdir(exist_ok=True)
        self.config = {'ghidra_home': ghidra_home, 'java_home': java_home, 'rizin_path': rizin_path}
        self.lock = threading.RLock(); self.jobs = {}; self.events = {}
        # Serialize provider operations, including cached-project access.
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='trex-analysis')
        for file in self.directory.glob('*.json'):
            record = json.loads(file.read_text(encoding='utf-8'))
            if record.get('status') in ('queued', 'running', 'cancelling'):
                record.update(status='interrupted', error='Previous server ended. Inspect retained output; no automatic rerun.')
                re_tools.write_json(file, record)
            self.jobs[record['job_id']] = record

    def path(self, value):
        p = Path(value).expanduser()
        p = (self.root / p).resolve() if not p.is_absolute() else p.resolve()
        if not p.is_relative_to(self.root):
            raise ValueError('Path is outside the configured investigation workspace')
        return p

    def _save(self, record):
        re_tools.write_json(self.directory / (record['job_id'] + '.json'), record)

    def start(self, action, target=None, analysis=None, provider=None, functions=None, limits=None):
        if action not in ('analyze', 'function') or provider not in (None, 'ghidra', 'rizin'):
            raise ValueError('Unknown action or provider')
        if not isinstance(functions or [], list) or any(not isinstance(x, str) or len(x) > 1024 for x in (functions or [])):
            raise ValueError('Functions must be exact names or 0x addresses')
        values = dict(DEFAULTS)
        for key, value in (limits or {}).items():
            if key not in values or type(value) is not int or not 1 <= value <= MAXIMUMS[key]:
                raise ValueError('Invalid limit: ' + key)
            values[key] = value
        if action == 'function' and not functions:
            raise ValueError('Provide a function selector')
        target_path = self.path(target) if target is not None else None
        analysis_path = self.path(analysis) if analysis is not None else None
        if action == 'analyze' and (target_path is None or not target_path.is_file()):
            raise ValueError('Target must be an existing file')
        if action == 'function':
            if analysis_path is None:
                raise ValueError('Provide a saved analysis')
            source = json.loads((analysis_path / 'manifest.json').read_text(encoding='utf-8'))
            self.path(source['artifact']['path'])
            project = source['project']
            self.path(project.get('path', project.get('directory')))
            # Discover from server configuration/environment, never execute a
            # launcher solely because an imported manifest names that path.
            from re_rizin import doctor as rizin_doctor
            if source.get('provider', {}).get('name') == 'rizin':
                located = rizin_doctor(self.config['rizin_path'])
                if located['status'] != 'available':
                    raise ValueError('Configure an installed Rizin before querying saved projects')
                config = {**self.config, 'rizin_path': located['path']}
            else:
                located = re_tools.doctor(self.config['ghidra_home'], self.config['java_home'])
                if located['status'] != 'available':
                    raise ValueError('Configure Ghidra/JDK before querying saved projects')
                config = {**self.config, 'ghidra_home': located['ghidra_home']}
        else:
            config = self.config
        with self.lock:
            if sum(j['status'] in ('queued', 'running', 'cancelling') for j in self.jobs.values()) >= 8:
                raise ValueError('Job queue full; finish or cancel existing jobs')
            job_id = uuid.uuid4().hex
            output = self.directory / (job_id + '-evidence')
            event = threading.Event(); self.events[job_id] = event
            record = {'job_id': job_id, 'status': 'queued', 'action': action, 'provider': provider,
                      'target': str(target_path) if target_path else None,
                      'analysis': str(analysis_path) if analysis_path else None, 'output': str(output)}
            self.jobs[job_id] = record; self._save(record)
            args = SimpleNamespace(action=action, target=str(target_path), analysis=str(analysis_path),
                                   provider=provider, output=str(output), function=functions or [],
                                   cancel_event=event, **config, **values)
            self.pool.submit(self._run, job_id, args)
            return dict(record)

    def _run(self, job_id, args):
        event = self.events[job_id]
        with self.lock:
            record = self.jobs[job_id]
            if event.is_set():
                record['status'] = 'cancelled'; self._save(record); return
            record['status'] = 'running'; self._save(record)
        try:
            result = re_tools.dispatch(args)
            with self.lock:
                record.update(status='cancelled' if event.is_set() else result.get('status', 'failed'), result=result)
                self._save(record)
        except Exception as exc:
            with self.lock:
                record.update(status='cancelled' if event.is_set() else 'failed', error=str(exc)); self._save(record)

    def status(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise ValueError('Unknown job ID')
            # Return a detached JSON snapshot, not a mutable shared record.
            return json.loads(json.dumps(self.jobs[job_id]))

    def cancel(self, job_id):
        with self.lock:
            record = self.status(job_id)
            if record['status'] in ('queued', 'running', 'cancelling'):
                self.events[job_id].set(); self.jobs[job_id]['status'] = 'cancelling'; self._save(self.jobs[job_id])
            return self.status(job_id)

    def close(self):
        for event in self.events.values():
            event.set()
        self.pool.shutdown(wait=True)


def create_server(jobs):
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    def errors(fn):
        @wraps(fn)
        def guarded(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise ToolError(str(exc)) from exc
        return guarded
    @asynccontextmanager
    async def lifespan(server):
        try:
            yield {}
        finally:
            await asyncio.to_thread(jobs.close)
    server = MCPServer('T-REX', version='3.3', lifespan=lifespan,
                       instructions='Start bounded analysis jobs, poll status, then read verified evidence pages. Partial results require checking coverage and capability gaps. Attach supported findings to the investigation checkpoint; exported data is not itself a final report.')

    @server.tool()
    @errors
    def doctor(provider: str = 'all') -> dict[str, Any]:
        """Check local Ghidra/JDK and Rizin installations; report shallow GUI discovery and install guidance."""
        if provider not in ('ghidra', 'rizin', 'all'):
            raise ValueError('Unknown provider')
        return re_tools.dispatch(SimpleNamespace(action='doctor', provider=provider, **jobs.config))

    @server.tool()
    @errors
    def analyze(target: str, provider: str = 'ghidra', functions: list[str] | None = None,
                limits: dict[str, int] | None = None) -> dict[str, Any]:
        """Start a static binary analysis job; return its ID immediately. Target paths are relative to the configured workspace. Provider: ghidra or rizin."""
        return jobs.start('analyze', target=target, provider=provider, functions=functions, limits=limits)

    @server.tool()
    @errors
    def function(analysis: str, functions: list[str], limits: dict[str, int] | None = None) -> dict[str, Any]:
        """Start a query from a saved analysis without reanalysis. Infer its provider and verify target/project identity."""
        return jobs.start('function', analysis=analysis, functions=functions, limits=limits)

    @server.tool()
    @errors
    def job_status(job_id: str) -> dict[str, Any]:
        """Read durable job state and result location. Interrupted jobs are never silently rerun."""
        return jobs.status(job_id)

    @server.tool()
    @errors
    def cancel_job(job_id: str) -> dict[str, Any]:
        """Request cancellation; poll until cancelled. Stop the provider process and retain existing evidence/logs."""
        return jobs.cancel(job_id)

    @server.tool()
    @errors
    def list_jobs() -> dict[str, Any]:
        """List the newest 50 jobs. Use job_status for details."""
        with jobs.lock:
            return {'jobs': [{k: v for k, v in j.items() if k != 'result'} for j in list(jobs.jobs.values())[-50:]]}

    @server.tool()
    @errors
    def view(analysis: str, kind: str, contains: str | None = None, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Read a hash-verified evidence page: functions, strings, symbols, segments or details. Filter, paginate and inspect collection coverage."""
        if kind not in re_tools.KINDS or not 1 <= limit <= 100 or offset < 0:
            raise ValueError('Invalid page parameters')
        result = re_tools.view(SimpleNamespace(analysis=str(jobs.path(analysis)), kind=kind,
                                               contains=contains, offset=offset, limit=limit))
        if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > 512 * 1024:
            raise ValueError('Page exceeds 512 KiB; lower limit, add a filter, or query with smaller detail bounds')
        return result
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, help='Existing investigation workspace for targets, evidence and durable jobs')
    parser.add_argument('--ghidra-home'); parser.add_argument('--java-home'); parser.add_argument('--rizin-path')
    args = parser.parse_args()
    jobs = Jobs(**vars(args))
    def stop(signum, frame):
        jobs.close()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    try:
        create_server(jobs).run(transport='stdio')
    finally:
        jobs.close()


if __name__ == '__main__':
    main()
