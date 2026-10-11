#!/usr/bin/env python3
"""Control-plane tests; GHIDRA_HOME enables additional real headless integration tests."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import re_tools as tools


def args_for(target, output, **kw):
    values = dict(target=str(target), output=str(output), ghidra_home=None, java_home=None,
                  function=['retry_delay_ms'], max_items=5000, max_functions=10,
                  max_instructions=2000, max_refs=1000, max_text_chars=4096,
                  max_pseudocode_chars=100000, decompile_timeout=30, analysis_timeout=60,
                  timeout=120)
    values.update(kw)
    return argparse.Namespace(**values)


def pe_fixture(path):
    """Minimal PE64: entry point returns 42; constructed here, never downloaded or executed."""
    image = bytearray(1024)
    image[:2] = b'MZ'
    struct.pack_into('<I', image, 0x3c, 0x80)
    image[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', image, 0x84, 0x8664, 1, 0, 0, 0, 240, 0x22)
    opt = 0x98
    struct.pack_into('<H', image, opt, 0x20b)
    struct.pack_into('<III', image, opt + 4, 512, 0, 0)
    struct.pack_into('<IIQII', image, opt + 16, 0x1000, 0x1000, 0x140000000, 0x1000, 0x200)
    struct.pack_into('<HH', image, opt + 40, 6, 0)
    struct.pack_into('<II', image, opt + 56, 0x2000, 0x200)
    struct.pack_into('<HH', image, opt + 68, 3, 0)
    struct.pack_into('<QQQQII', image, opt + 72, 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    section = opt + 240
    image[section:section+8] = b'.text\0\0\0'
    struct.pack_into('<IIIIIIHHI', image, section + 8, 6, 0x1000, 512, 512, 0, 0, 0, 0, 0x60000020)
    image[512:518] = bytes.fromhex('b82a000000c3')
    path.write_bytes(image)


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.target = self.work / 'target with spaces'
        self.target.write_bytes(b'fixture')

    def tearDown(self):
        self.temp.cleanup()

    def found(self):
        return dict(status='available', launcher='/tools/headless', ghidra_home='/tools',
                    version='test', java={'major': 21})

    def fake_export(self, command, output, timeout, java_home):
        request = json.loads((output / 'request.json').read_text())
        tools.write_json(output / 'metadata.json', {
            'run_id': request['run_id'], 'program': self.target.name,
            'program_sha256': request['expected_sha256'], 'analysis_timed_out': False,
            'collections': {'functions': {'coverage': 'complete'}}})
        (output / 'functions.jsonl').write_text('{"name":"alpha"}\n{"name":"beta"}\n{"name":"alpha2"}\n')
        (Path(command[1]) / (command[2] + '.gpr')).touch()
        database = Path(command[1]) / (command[2] + '.rep') / 'idata'
        database.mkdir(parents=True, exist_ok=True)
        (database / 'program.gbf').write_bytes(b'database')
        return 0, False

    def run_fake(self, side_effect=None, **kw):
        output = self.work / 'analysis'
        with patch.object(tools, 'doctor', return_value=self.found()), \
             patch.object(tools, 'run_process', side_effect=side_effect or self.fake_export):
            result = tools.analyze(args_for(self.target, output, **kw))
        return result, output

    def test_empty_property_does_not_swallow_next_line(self):
        p = self.work / 'props'
        p.write_text('application.java.max=\napplication.java.min=21\n# ignored=1\n')
        self.assertEqual(tools.properties(p)['application.java.min'], '21')

    def test_explicit_invalid_home_does_not_fall_back(self):
        self.assertEqual(tools.find_ghidra(str(self.work / 'absent')), (None, None))

    def test_doctor_rejects_old_java(self):
        home = self.work / 'ghidra'
        (home / 'support').mkdir(parents=True)
        (home / 'Ghidra').mkdir()
        (home / 'support' / ('analyzeHeadless.bat' if os.name == 'nt' else 'analyzeHeadless')).touch()
        (home / 'Ghidra/application.properties').write_text('application.version=12.1.4\napplication.java.max=\napplication.java.min=21\n')
        with patch.object(tools.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', 'openjdk version "17.0.1"')):
            found = tools.doctor(str(home), str(self.work / 'java'))
        self.assertEqual(found['minimum_java'], 21)
        self.assertEqual(found['status'], 'unavailable')

    def test_success_identity_manifest_and_spaces(self):
        result, output = self.run_fake()
        m = json.loads((output / 'manifest.json').read_text())
        self.assertEqual(result['status'], 'success')
        self.assertEqual(m['artifact']['sha256'], tools.sha256(self.target))
        self.assertIn(str(self.target), m['command'])
        self.assertIn('functions.jsonl', m['files'])

    def test_zero_exit_without_export_fails(self):
        result, _ = self.run_fake(lambda *args: (0, False))
        self.assertEqual(result['status'], 'failed')

    def test_wrong_project_identity_fails(self):
        def exporter(*args):
            ret = self.fake_export(*args)
            p = args[1] / 'metadata.json'
            m = json.loads(p.read_text()); m['program_sha256'] = '0' * 64
            tools.write_json(p, m)
            return ret
        result, _ = self.run_fake(exporter)
        self.assertEqual(result['status'], 'failed')

    def test_target_mutation_during_run_fails(self):
        def exporter(*args):
            ret = self.fake_export(*args)
            self.target.write_bytes(b'changed')
            return ret
        result, _ = self.run_fake(exporter)
        self.assertEqual(result['status'], 'failed')

    def test_truncated_export_is_partial(self):
        def exporter(*args):
            ret = self.fake_export(*args)
            p = args[1] / 'metadata.json'
            m = json.loads(p.read_text()); m['collections']['functions']['coverage'] = 'partial'
            tools.write_json(p, m)
            return ret
        result, _ = self.run_fake(exporter)
        self.assertEqual(result['status'], 'partial')

    def test_view_pages_filters_and_checks_integrity(self):
        _, output = self.run_fake()
        a = argparse.Namespace(analysis=str(output), kind='functions', contains='alpha', offset=0, limit=1)
        page = tools.view(a)
        self.assertEqual(page['matches_in_export'], 2)
        self.assertEqual(page['next_offset'], 1)
        a.offset = 1
        self.assertEqual(tools.view(a)['rows'][0]['name'], 'alpha2')
        (output / 'functions.jsonl').write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            tools.view(a)

    def test_existing_output_is_preserved(self):
        _, output = self.run_fake()
        with patch.object(tools, 'doctor', return_value=self.found()), self.assertRaises(FileExistsError):
            tools.analyze(args_for(self.target, output))

    def test_reuse_rejects_target_drift(self):
        _, output = self.run_fake()
        self.target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            tools.analyze(args_for(self.target, self.work / 'next', analysis=str(output)), reuse=True)

    def test_reuse_rejects_project_drift(self):
        _, output = self.run_fake()
        m = json.loads((output / 'manifest.json').read_text())
        p = Path(m['project']['directory']) / (m['project']['name'] + '.rep') / 'idata/program.gbf'
        p.write_bytes(b'changed database')
        with patch.object(tools, 'doctor', return_value=self.found()), self.assertRaisesRegex(ValueError, 'database changed'):
            tools.analyze(args_for(self.target, self.work / 'next', analysis=str(output)), reuse=True)

    def test_reuse_is_readonly_and_does_not_reanalyze(self):
        _, output = self.run_fake()
        with patch.object(tools, 'doctor', return_value=self.found()), \
             patch.object(tools, 'run_process', side_effect=self.fake_export) as run:
            result = tools.analyze(args_for(self.target, self.work / 'next', analysis=str(output)), reuse=True)
        command = run.call_args.args[0]
        self.assertIn('-noanalysis', command)
        self.assertIn('-readOnly', command)
        self.assertNotIn('-import', command)
        self.assertEqual(result['status'], 'success')

    def test_process_timeout_terminates(self):
        output = self.work / 'logs'; output.mkdir()
        code, timed_out = tools.run_process([sys.executable, '-c', 'import time; time.sleep(30)'], output, 0.1)
        self.assertTrue(timed_out)
        self.assertNotEqual(code, 0)

    def test_windows_command_preserves_spaces_and_rejects_expansion(self):
        command = tools.windows_command(['C:/Tools With Spaces/headless.bat', 'a&b', 'two words'])
        self.assertIn('"a&b"', command[-1])
        with self.assertRaises(ValueError):
            tools.windows_command(['C:/%USERNAME%/headless.bat'])


@unittest.skipUnless(os.environ.get('GHIDRA_HOME'), 'Set GHIDRA_HOME for real Ghidra tests')
class GhidraIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='trex ghidra ')
        self.work = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def live(self, target, output, **kw):
        result = tools.analyze(args_for(target, output, ghidra_home=os.environ['GHIDRA_HOME'],
                                       java_home=os.environ.get('JAVA_HOME'), **kw))
        self.assertIn(result['status'], ('success', 'partial'), result)
        return result

    def test_pe64_bytes_addresses_decompile_and_cached_query(self):
        target = self.work / 'fixture.exe'; pe_fixture(target)
        output = self.work / 'analysis'
        result = self.live(target, output, function=['0x140001000'])
        detail = json.loads((output / 'details.jsonl').read_text())
        self.assertEqual(detail['instructions'][0]['bytes'], 'b82a000000')
        self.assertEqual(detail['rva'], '0x1000')
        self.assertEqual(detail['decompile_status'], 'success')
        self.assertIn('0x2a', detail['pseudocode'].lower())
        self.assertEqual(result['metadata']['program_sha256'], tools.sha256(target))
        a = args_for(target, self.work / 'cached', analysis=str(output), function=['0x140001000'],
                     ghidra_home=os.environ['GHIDRA_HOME'], java_home=os.environ.get('JAVA_HOME'))
        cached = tools.analyze(a, reuse=True)
        self.assertEqual(cached['status'], 'success', cached)
        self.assertFalse((self.work / 'cached/functions.jsonl').exists())
        a.output = str(self.work / 'missing'); a.function = ['missing_function']
        missing = tools.analyze(a, reuse=True)
        self.assertEqual(missing['status'], 'partial')
        self.assertEqual(missing['metadata']['collections']['details']['unresolved_selectors'], ['missing_function'])

    @unittest.skipUnless(os.name != 'nt' and shutil.which('cc'), 'Requires Unix C compiler')
    def test_elf_retry_logic_and_bounds(self):
        source = tools.ROOT.parents[1] / 'examples/retry-policy/retry_policy.c'
        target = self.work / 'retry-policy'
        subprocess.run(['cc', '-O0', '-g', str(source), '-o', str(target)], check=True)
        output = self.work / 'analysis'
        self.live(target, output)
        detail = json.loads((output / 'details.jsonl').read_text())
        self.assertEqual(detail['name'], 'retry_delay_ms')
        self.assertIn('0x96', detail['pseudocode'])
        self.assertTrue(any(r['type'] == 'UNCONDITIONAL_CALL' for r in detail['incoming_references']))
        a = args_for(target, self.work / 'bounded', analysis=str(output),
                     ghidra_home=os.environ['GHIDRA_HOME'], java_home=os.environ.get('JAVA_HOME'),
                     max_instructions=1, max_refs=1, max_pseudocode_chars=10)
        bounded = tools.analyze(a, reuse=True)
        self.assertEqual(bounded['status'], 'partial')
        detail = json.loads((self.work / 'bounded/details.jsonl').read_text())
        self.assertEqual(len(detail['instructions']), 1)
        self.assertTrue(detail['pseudocode_truncated'])
        self.assertEqual(detail['instructions_coverage'], 'partial')

    @unittest.skipUnless(os.name != 'nt' and shutil.which('cc'), 'Requires Unix C compiler')
    def test_optimized_stripped_elf_and_inventory_caps(self):
        source = tools.ROOT.parents[1] / 'examples/retry-policy/retry_policy.c'
        target = self.work / 'retry-stripped'
        subprocess.run(['cc', '-O2', '-s', '-no-pie', str(source), '-o', str(target)], check=True)
        entry = struct.unpack_from('<Q', target.read_bytes(), 24)[0]
        output = self.work / 'analysis'
        result = self.live(target, output, function=[hex(entry)], max_items=1, max_text_chars=2)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['metadata']['collections']['functions']['exported'], 1)
        self.assertEqual(result['metadata']['collections']['functions']['coverage'], 'partial')
        for kind in ('functions', 'strings', 'symbols', 'segments'):
            self.assertLessEqual(len((output / (kind + '.jsonl')).read_text().splitlines()), 1)
        strings = [json.loads(line) for line in (output / 'strings.jsonl').read_text().splitlines()]
        self.assertTrue(strings[0]['value_truncated'])
        self.assertEqual(len(strings[0]['value']), 2)
        detail = json.loads((output / 'details.jsonl').read_text())
        self.assertEqual(int(detail['address'], 16), entry)
        self.assertEqual(detail['decompile_status'], 'success')


if __name__ == '__main__':
    unittest.main()
