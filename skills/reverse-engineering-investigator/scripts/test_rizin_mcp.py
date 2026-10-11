#!/usr/bin/env python3
"""Real Rizin and MCP transport checks; skip unavailable optional runtimes explicitly."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import re_mcp
import re_rizin
import re_tools
from test_tools import args_for, pe_fixture


def wait_job(jobs, job_id):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        value = jobs.status(job_id)
        if value['status'] not in ('queued', 'running', 'cancelling'):
            return value
        time.sleep(0.01)
    raise AssertionError('Job did not finish')


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.work = Path(self.temp.name).resolve()
        self.target = self.work / 'target'; self.target.write_bytes(b'test')
        self.jobs = re_mcp.Jobs(self.work)

    def tearDown(self):
        self.jobs.close(); self.temp.cleanup()

    def test_path_escape_and_invalid_limits(self):
        with self.assertRaises(ValueError): self.jobs.path('../elsewhere')
        with self.assertRaises(ValueError): self.jobs.start('analyze', target='target', limits={'timeout': 0})
        with self.assertRaises(ValueError): self.jobs.start('analyze', target='target', limits={'unknown': 3})
        with self.assertRaises(ValueError): self.jobs.start('function', analysis='missing', functions=[])

    def test_job_persistence_and_cancel(self):
        entered = threading.Event()
        def fake(args):
            entered.set(); args.cancel_event.wait(5)
            return {'status': 'failed', 'output': args.output}
        with patch.object(re_tools, 'dispatch', side_effect=fake):
            job = self.jobs.start('analyze', target='target')
            self.assertTrue(entered.wait(3))
            self.jobs.cancel(job['job_id'])
            self.assertEqual(wait_job(self.jobs, job['job_id'])['status'], 'cancelled')
        self.jobs.close()
        self.jobs = re_mcp.Jobs(self.work)
        self.assertEqual(self.jobs.status(job['job_id'])['status'], 'cancelled')

    def test_restart_marks_unfinished_interrupted(self):
        re_tools.write_json(self.jobs.directory / 'prior.json', {'job_id': 'prior', 'status': 'running'})
        self.jobs.close(); self.jobs = re_mcp.Jobs(self.work)
        self.assertEqual(self.jobs.status('prior')['status'], 'interrupted')

    def test_cancel_stops_real_process(self):
        out = self.work / 'logs'; out.mkdir(); event = threading.Event()
        timer = threading.Timer(0.1, event.set); timer.start()
        try:
            code, interrupted = re_tools.run_process([sys.executable, '-c', 'import time; time.sleep(30)'], out, 60, cancel_event=event)
        finally:
            timer.cancel()
        self.assertTrue(interrupted); self.assertNotEqual(code, 0)

    def test_explicit_invalid_rizin_does_not_fallback(self):
        self.assertEqual(re_rizin.doctor(str(self.work / 'missing'))['status'], 'unavailable')

    def test_rizin_pipe_cancel_stops_hung_process(self):
        popen = subprocess.Popen
        created = []
        def launch(*args, **kwargs):
            proc = popen([sys.executable, '-c', 'import sys,time;sys.stdout.buffer.write(bytes([0]));sys.stdout.flush();sys.stdin.readline();time.sleep(30)'], **kwargs)
            created.append(proc); return proc
        event = threading.Event()
        with patch.object(re_rizin.subprocess, 'Popen', side_effect=launch):
            pipe = re_rizin.RizinPipe('ignored', self.target, self.work, 60, event)
            timer = threading.Timer(0.1, event.set); timer.start()
            try:
                with self.assertRaises(InterruptedError): pipe.cmd('aaa')
            finally:
                timer.cancel(); pipe.close()
        self.assertIsNotNone(created[0].poll())

    def test_project_paths_reject_command_substitution(self):
        self.assertIn('two words', re_rizin.quote_path('two words/project.rzdb'))
        for name in ['`id`', 'a\nq', '$()']:
            with self.assertRaises(ValueError): re_rizin.quote_path(name)


@unittest.skipUnless(os.environ.get('RIZIN_PATH'), 'Set RIZIN_PATH for real Rizin tests')
class RizinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='trex rizin ')
        self.work = Path(self.temp.name).resolve(); self.target = self.work / 'fixture.exe'; pe_fixture(self.target)

    def tearDown(self):
        self.temp.cleanup()

    def run_analysis(self, output, **kw):
        result = re_rizin.analyze(args_for(self.target, output, rizin_path=os.environ['RIZIN_PATH'], **kw))
        self.assertIn(result['status'], ('success', 'partial'), result)
        return result

    def test_pe_bytes_project_cache_and_missing_selector(self):
        out = self.work / 'analysis'; self.run_analysis(out, function=['0x140001000'])
        detail = json.loads((out / 'details.jsonl').read_text())
        self.assertEqual(detail['instructions'][0]['bytes'], 'b82a000000')
        self.assertEqual(detail['instructions'][0]['file_offset'], 0x200)
        self.assertEqual(detail['instructions'][0]['byte_verification'], 'match')
        self.assertEqual(detail['instructions'][0]['rva'], '0x1000')
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(manifest['artifact']['sha256'], re_tools.sha256(self.target))
        project = Path(manifest['project']['path']); old = project.read_bytes()
        result = re_rizin.analyze(args_for(None, self.work / 'query', analysis=str(out), function=['0x140001000'], rizin_path=os.environ['RIZIN_PATH']), True)
        self.assertIn(result['status'], ('success', 'partial'), result)
        self.assertEqual(project.read_bytes(), old)
        self.assertNotIn('aaa', (self.work / 'query/commands.jsonl').read_text())
        self.run_analysis(self.work / 'missing', function=['absent'])
        metadata = json.loads((self.work / 'missing/metadata.json').read_text())
        self.assertEqual(metadata['collections']['details']['unresolved_selectors'], ['absent'])
        project.write_bytes(b'changed project')
        with self.assertRaises(ValueError):
            re_rizin.analyze(args_for(None, self.work / 'bad-project', analysis=str(out), function=['0x140001000'], rizin_path=os.environ['RIZIN_PATH']), True)

    def test_caps_view_and_drift(self):
        out = self.work / 'analysis'; self.run_analysis(out, function=['0x140001000'], max_items=1, max_instructions=1)
        detail = json.loads((out / 'details.jsonl').read_text())
        self.assertEqual(detail['instructions_coverage'], 'partial')
        self.assertEqual(len(detail['instructions']), 1)
        args = SimpleNamespace(analysis=str(out), kind='details', contains=None, offset=0, limit=1)
        self.assertEqual(len(re_tools.view(args)['rows']), 1)
        (out / 'details.jsonl').write_text('{}\n')
        with self.assertRaises(ValueError): re_tools.view(args)
        self.target.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            re_rizin.analyze(args_for(None, self.work / 'drift', analysis=str(out), function=['0x140001000'], rizin_path=os.environ['RIZIN_PATH']), True)

    @unittest.skipUnless(shutil.which('cc') and os.name != 'nt', 'Requires Unix C compiler')
    def test_elf_callers_and_byte_checks(self):
        root = Path(__file__).resolve().parents[3]
        self.target = self.work / 'retry'
        subprocess.run(['cc', '-O0', '-g', str(root / 'examples/retry-policy/retry_policy.c'), '-o', str(self.target)], check=True)
        out = self.work / 'analysis'; self.run_analysis(out, function=['0x1149'])
        # Query the discovered symbol instead of depending on a compiler's chosen entry address.
        functions = [json.loads(x) for x in (out / 'functions.jsonl').read_text().splitlines()]
        helper = next(f for f in functions if f['name'].endswith('.retry_delay_ms'))
        query = self.work / 'query'
        result = re_rizin.analyze(args_for(None, query, analysis=str(out), function=[helper['address']], rizin_path=os.environ['RIZIN_PATH']), True)
        self.assertIn(result['status'], ('success', 'partial'), result)
        detail = json.loads((query / 'details.jsonl').read_text())
        self.assertEqual(sum(r['type'] == 'CALL' for r in detail['incoming_references']), 4)
        self.assertTrue(all(i['byte_verification'] == 'match' for i in detail['instructions']))
        self.assertTrue(any('0x96' in i['text'] for i in detail['instructions']))


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install requirements-mcp.txt for MCP transport tests')
class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_discovery_validation_and_real_job(self):
        from mcp import Client, StdioServerParameters
        with tempfile.TemporaryDirectory(prefix='trex mcp ') as temp:
            target = Path(temp) / 'fixture.exe'; pe_fixture(target)
            params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name('re_mcp.py')), '--workspace', temp], env=dict(os.environ))
            async with Client(params) as client:
                names = {t.name for t in (await client.list_tools()).tools}
                self.assertEqual(names, {'doctor', 'analyze', 'function', 'view', 'job_status', 'cancel_job', 'list_jobs'})
                invalid = await client.call_tool('view', {'analysis': '../outside', 'kind': 'details'})
                self.assertTrue(invalid.is_error)
                if os.environ.get('RIZIN_PATH'):
                    started = await client.call_tool('analyze', {'target': 'fixture.exe', 'provider': 'rizin', 'functions': ['0x140001000']})
                    self.assertFalse(started.is_error, started)
                    job_id = started.structured_content['job_id']
                    for _ in range(300):
                        status = (await client.call_tool('job_status', {'job_id': job_id})).structured_content
                        if status['status'] not in ('queued', 'running', 'cancelling'):
                            break
                        await asyncio.sleep(0.1)
                    self.assertIn(status['status'], ('success', 'partial'), status)
                    viewed = await client.call_tool('view', {'analysis': status['output'], 'kind': 'details', 'limit': 1})
                    self.assertFalse(viewed.is_error, viewed)
                    self.assertEqual(viewed.structured_content['rows'][0]['instructions'][0]['bytes'], 'b82a000000')


if __name__ == '__main__':
    unittest.main(verbosity=2)
