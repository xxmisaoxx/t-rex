#!/usr/bin/env python3
"""Package/state portability checks; these do not launch the named products."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from export_host import ROOT, export, relative_path
from re_state import load, mutate, reset_context, validate
from test_state import fixture
from validate_package import validate as validate_package


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.source = self.work / 'source'
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns('__pycache__'))

    def tearDown(self):
        self.temp.cleanup()

    def refresh_manifest(self):
        m = json.loads((self.source / 'MANIFEST.json').read_text())
        m['files'] = {p.relative_to(self.source).as_posix(): {
            'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in self.source.rglob('*') if p.is_file() and p.name != 'MANIFEST.json'}
        (self.source / 'MANIFEST.json').write_text(json.dumps(m))

    def test_all_documented_layouts_preserve_complete_tree(self):
        expected = {
            'opencode': ('.opencode/skills', '.config/opencode/skills'),
            'claude-code': ('.claude/skills', '.claude/skills'),
            'codex': ('.agents/skills', '.agents/skills'),
            'cursor': ('.cursor/skills', '.cursor/skills'),
            'antigravity': ('.agents/skills', '.gemini/config/skills'),
            'antigravity-cli': ('.agents/skills', '.gemini/antigravity-cli/skills'),
            'pi': ('.agents/skills', '.agents/skills'),
            'shared': ('.agents/skills', '.agents/skills'),
            'generic': ('skills', None)}
        for host, paths in expected.items():
            for scope, layout in zip(('project', 'user'), paths):
                if layout is None:
                    continue
                with self.subTest(host=host, scope=scope):
                    out = self.work / (host + '-' + scope)
                    result = export(host, out, scope, self.source)
                    target = out / layout / 'reverse-engineering-investigator'
                    self.assertEqual(result['skill_path'], target.relative_to(out).as_posix())
                    self.assertFalse(result['installed'])
                    self.assertEqual(validate_package(target), [])
                    for name in json.loads((self.source / 'MANIFEST.json').read_text())['files']:
                        self.assertEqual((target / name).read_bytes(), (self.source / name).read_bytes())
                    pointer = ('~/' if scope == 'user' else '') + result['skill_path'] + '/SKILL.md'
                    self.assertIn(pointer, (out / 'LOADER.fragment.md').read_text())

    def test_existing_output_preserved(self):
        out = self.work / 'existing'; out.mkdir()
        sentinel = out / 'AGENTS.md'; sentinel.write_text('existing policy')
        with self.assertRaises(ValueError): export('codex', out, source=self.source)
        self.assertEqual(sentinel.read_text(), 'existing policy')
        self.assertEqual(list(out.iterdir()), [sentinel])

    def test_unknown_host_no_write(self):
        out = self.work / 'unknown'
        with self.assertRaises(ValueError): export('made-up', out, source=self.source)
        self.assertFalse(out.exists())

    def test_generic_user_scope_no_write(self):
        out = self.work / 'generic-user'
        with self.assertRaises(ValueError): export('generic', out, 'user', self.source)
        self.assertFalse(out.exists())

    def test_invalid_scope_no_write(self):
        with self.assertRaises(ValueError): export('codex', self.work / 'bad-scope', 'admin', self.source)

    def test_source_overlap_no_write(self):
        out = self.source / 'export'
        with self.assertRaises(ValueError): export('codex', out, source=self.source)
        self.assertFalse(out.exists())

    def test_changed_source_rejected(self):
        (self.source / 'SKILL.md').write_text('changed after manifest')
        out = self.work / 'changed'
        with self.assertRaises(ValueError): export('codex', out, source=self.source)
        self.assertFalse(out.exists())

    def test_missing_source_rejected(self):
        (self.source / 'profiles/windows-pe.md').unlink()
        with self.assertRaises(ValueError): export('opencode', self.work / 'missing', source=self.source)

    def test_unsafe_manifest_path_rejected(self):
        path = self.source / 'MANIFEST.json'; m = json.loads(path.read_text())
        m['files']['../outside.txt'] = {'size': 0, 'sha256': '0' * 64}; path.write_text(json.dumps(m))
        with self.assertRaises(ValueError): export('codex', self.work / 'unsafe', source=self.source)

    def test_unsafe_layout_rejected(self):
        path = self.source / 'hosts/registry.json'; r = json.loads(path.read_text())
        r['hosts']['codex']['project'] = '../escape'; path.write_text(json.dumps(r)); self.refresh_manifest()
        with self.assertRaises(ValueError): export('codex', self.work / 'unsafe-layout', source=self.source)

    def test_relative_path_rejects_platform_escape(self):
        for value in ('/tmp/a', '../a', 'a/../b', 'a//b', './a', 'C:/a', 'a\\b', ''):
            with self.subTest(value=value), self.assertRaises(ValueError): relative_path(value)

    def test_dangling_output_symlink_preserved(self):
        out = self.work / 'link'
        try: out.symlink_to(self.work / 'missing-destination')
        except OSError as exc: self.skipTest('symlink creation unavailable: ' + str(exc))
        with self.assertRaises(ValueError): export('pi', out, source=self.source)
        self.assertTrue(out.is_symlink()); self.assertFalse(out.exists())

    def test_symlinked_source_rejected(self):
        path = self.source / 'README.md'; outside = self.work / 'outside.md'
        outside.write_bytes(path.read_bytes()); path.unlink()
        try: path.symlink_to(outside)
        except OSError as exc: self.skipTest('symlink creation unavailable: ' + str(exc))
        with self.assertRaises(ValueError): export('cursor', self.work / 'symlink', source=self.source)

    def test_cli_export(self):
        out = self.work / 'cli'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/export_host.py'), '--host', 'claude-code', '--out', str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['host'], 'claude-code')
        self.assertTrue((out / '.claude/skills/reverse-engineering-investigator/SKILL.md').is_file())

    def test_cli_rejects_unknown_host(self):
        out = self.work / 'unknown-cli'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/export_host.py'), '--host', 'unknown', '--out', str(out)], capture_output=True)
        self.assertNotEqual(result.returncode, 0); self.assertFalse(out.exists())

    def state(self):
        path = self.work / 'target.bin'; s = fixture(path)
        s['context'].update(capacity_tokens=1000000, used_tokens=780000, next_cost_tokens=12000,
                            future_reserve_tokens=25000, margin_tokens=20000, telemetry_current=True)
        return s

    def test_context_reset_preserves_all_knowledge(self):
        s = self.state(); original = copy.deepcopy(s); reset_context(s); validate(s)
        for name in original:
            if name != 'context': self.assertEqual(s[name], original[name])
        for name, value in s['context'].items():
            if name.endswith('_tokens'): self.assertIsNone(value)
        self.assertFalse(s['context']['telemetry_current']); self.assertTrue(s['context']['durable'])

    def test_context_reset_atomic_checkpoint(self):
        path = self.work / 'INVESTIGATION.json'; s = self.state(); path.write_text(json.dumps(s))
        mutate(path, 0, reset_context); after = load(path)
        self.assertEqual(after['checkpoint_revision'], 1); self.assertTrue(after['context']['durable'])
        self.assertEqual(after['next_probe'], s['next_probe']); self.assertEqual(after['evidence'], s['evidence'])

    def test_context_reset_conflict_preserves_bytes(self):
        path = self.work / 'INVESTIGATION.json'; path.write_text(json.dumps(self.state())); before = path.read_bytes()
        with self.assertRaises(ValueError): mutate(path, 9, reset_context)
        self.assertEqual(path.read_bytes(), before)

    def test_context_reset_writer_lock_preserves_bytes(self):
        path = self.work / 'INVESTIGATION.json'; path.write_text(json.dumps(self.state())); before = path.read_bytes()
        path.with_name(path.name + '.lock').write_text('another host still writing')
        with self.assertRaises(ValueError): mutate(path, 0, reset_context)
        self.assertEqual(path.read_bytes(), before)

    def test_relative_artifact_paths_survive_workspace_copy(self):
        original = self.work / 'original'; original.mkdir(); s = fixture(original / 'target.bin')
        s['artifacts'][0]['path'] = 'target.bin'; (original / 'INVESTIGATION.json').write_text(json.dumps(s))
        moved = self.work / 'relocated'; shutil.copytree(original, moved)
        state = load(moved / 'INVESTIGATION.json'); self.assertTrue(validate(state, moved, True))
        (moved / 'target.bin').write_bytes(b'changed on destination host')
        with self.assertRaises(ValueError): validate(state, moved, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
