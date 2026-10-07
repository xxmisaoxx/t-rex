#!/usr/bin/env python3
"""Structural checks only: files, manifest, local links and template schema."""
import json,hashlib,re,sys
from pathlib import Path
def validate(root):
    root=Path(root); errors=[]
    m=json.loads((root/'MANIFEST.json').read_text())
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in p.parts}
    if set(m['files'])!=actual: errors.append('manifest inventory mismatch')
    for name,info in m['files'].items():
        p=root/name
        if not p.is_file(): errors.append('missing '+name); continue
        b=p.read_bytes()
        if len(b)!=info['size'] or hashlib.sha256(b).hexdigest()!=info['sha256']: errors.append('manifest bytes '+name)
    for p in root.rglob('*.md'):
        for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
            if '://' in dest or dest.startswith('#'): continue
            if not (p.parent/dest.split('#')[0]).exists(): errors.append('broken link '+str(p.relative_to(root))+' '+dest)
    try:
        from schema_check import check
        for name in ('investigation','pe-map'):
            path=root/'schemas'/f'{name}.schema.json'
            if path.exists():
                template='INVESTIGATION.json' if name=='investigation' else 'PE-MAP.json'
                check(json.loads((root/'templates'/template).read_text()),json.loads(path.read_text()))
    except ImportError: errors.append('bundled schema_check unavailable')
    except Exception as exc: errors.append('schema: '+str(exc))
    core=(root/'SKILL.md').read_text()
    if not core.startswith('---\n') or 'name: reverse-engineering-investigator' not in core: errors.append('frontmatter')
    if len(core.splitlines())>200: errors.append('core budget exceeded')
    registry=root/'hosts/registry.json'
    if registry.exists():
        try:
            r=json.loads(registry.read_text())
            if r['release_version']!=m['version'] or r['skill_name']!=m['name']: errors.append('host registry release/name mismatch')
            for host,info in r['hosts'].items():
                if not (root/'hosts'/info['guide']).is_file(): errors.append('missing host guide '+host)
                for scope in ('project','user'):
                    layout=info[scope]
                    if layout is not None and (not isinstance(layout,str) or not layout or '\\' in layout or ':' in layout or layout.startswith('/') or any(x in ('','.','..') for x in layout.split('/'))): errors.append('unsafe host layout '+host)
        except (KeyError,TypeError,ValueError) as exc: errors.append('host registry: '+str(exc))
    return errors
if __name__=='__main__':
    errors=validate(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
    print(json.dumps({'level':'structural','errors':errors,'passed':not errors},indent=2))
    raise SystemExit(bool(errors))
