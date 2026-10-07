#!/usr/bin/env python3
"""Provider-neutral state mechanics. Does not execute target artifacts."""
import argparse,copy,hashlib,json,os,tempfile
from collections import deque
from pathlib import Path
from schema_check import check
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/investigation.schema.json').read_text())
def digest(path):
    h=hashlib.sha256();size=0
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b);size+=len(b)
    return h.hexdigest(),size
def load(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('duplicate JSON key '+k)
            d[k]=v
        return d
    def bad_constant(value): raise ValueError('nonstandard JSON constant '+value)
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=bad_constant)
def validate(s,base=None,verify=False):
    check(s,SCHEMA)
    tables={};allids=set()
    for group in ('artifacts','questions','hypotheses','evidence','probes'):
        table={}
        for item in s[group]:
            ident=item['id']
            if ident in allids: raise ValueError('duplicate ID '+ident)
            allids.add(ident);table[ident]=item
        tables[group]=table
    A,Q,E=tables['artifacts'],tables['questions'],tables['evidence']
    active=set(s['active_artifact_ids'])
    def refs(ids,table,label):
        if any(i not in table for i in ids): raise ValueError('dangling '+label)
    refs(active,A,'active artifact')
    for a in A.values():
        if a['parent_id'] is not None: refs([a['parent_id']],A,'parent')
        for r in a['changed_ranges']:
            if r['end']<=r['start']: raise ValueError('empty/inverted changed range')
    def acyclic(table,edges,label):
        done=set()
        for origin in table:
            if origin in done: continue
            visiting={origin};stack=[(origin,iter(edges(table[origin])))]
            while stack:
                node,it=stack[-1]
                dep=next(it,None)
                if dep is None:
                    visiting.remove(node);done.add(node);stack.pop();continue
                if dep in visiting: raise ValueError('cycle '+label)
                if dep not in done:
                    visiting.add(dep);stack.append((dep,iter(edges(table[dep]))))
    acyclic(A,lambda x:[x['parent_id']] if x['parent_id'] else [],'lineage')
    for e in E.values():
        refs(e['artifact_ids'],A,'evidence artifact');refs(e['dependencies'],E,'evidence dependency');refs(e['supersedes'],E,'supersedes')
        if e['id'] in e['supersedes']: raise ValueError('self supersession')
        if e['class']!='OBSERVED' and not e['dependencies']: raise ValueError('unsupported derived/inferred claim')
        if e['location']['domain']=='runtime-va' and e['runtime'] is None: raise ValueError('runtime location without boundary')
        if e['validity']=='current':
            if not set(e['artifact_ids'])<=active: raise ValueError('current claim on inactive revision')
            if any(E[d]['validity']!='current' for d in e['dependencies']): raise ValueError('current claim has noncurrent dependency')
    acyclic(E,lambda x:x['dependencies'],'evidence')
    acyclic(E,lambda x:x['supersedes'],'supersession')
    for q in Q.values():
        refs(q['evidence_ids'],E,'question evidence')
        if q['status']=='ANSWERED' and (not q['evidence_ids'] or any(E[i]['validity']!='current' for i in q['evidence_ids'])): raise ValueError('answered question lacks current support')
    for h in s['hypotheses']:
        refs([h['question_id']],Q,'hypothesis question');refs(h['evidence_ids'],E,'hypothesis evidence')
        if h['status'] in ('SUPPORTED','REJECTED') and (not h['evidence_ids'] or any(E[i]['validity']!='current' for i in h['evidence_ids'])): raise ValueError('hypothesis status lacks current support')
    for p in s['probes']:
        refs([p['question_id']],Q,'probe question');refs(p['artifact_ids'],A,'probe artifact')
    for m in s['maps']:
        refs([m['artifact_id']],A,'map artifact');refs(m['evidence_ids'],E,'map evidence')
    n=s['next_probe']
    if n:
        refs([n['question_id']],Q,'NEXT question');refs(n['artifact_ids'],A,'NEXT artifact')
        if Q[n['question_id']]['status'] not in ('PARTIAL','UNRESOLVED'): raise ValueError('NEXT question not open')
        if not set(n['artifact_ids'])<=active: raise ValueError('NEXT inactive revision')
    c=s['context']
    if c['capacity_tokens'] is not None and c['used_tokens'] is not None and (c['capacity_tokens']<=0 or c['used_tokens']>c['capacity_tokens']): raise ValueError('invalid context capacity/usage')
    if verify:
        base=Path(base or '.')
        for ident in active:
            a=A[ident];p=Path(a['path']);p=p if p.is_absolute() else base/p
            sha,size=digest(p)
            if sha!=a['sha256'] or size!=a['size']: raise ValueError('artifact drift '+ident)
    return True
def closure(s,roots):
    ids={e['id'] for e in s['evidence']}
    if not set(roots)<=ids: raise ValueError('unknown invalidation root')
    reverse={ident:[] for ident in ids}
    for e in s['evidence']:
        for dep in e['dependencies']: reverse[dep].append(e['id'])
    out=set(roots);pending=deque(roots)
    while pending:
        for ident in reverse[pending.popleft()]:
            if ident not in out: out.add(ident);pending.append(ident)
    return out
def reopen(s,affected):
    for q in s['questions']:
        if q['status']=='ANSWERED' and set(q['evidence_ids'])&affected: q['status']='PARTIAL'
    for h in s['hypotheses']:
        if h['status'] in ('SUPPORTED','REJECTED') and set(h['evidence_ids'])&affected: h['status']='UNTESTED'
    if s['next_probe'] and any(a not in s['active_artifact_ids'] for a in s['next_probe']['artifact_ids']): s['next_probe']=None
def invalidate(s,roots):
    affected=closure(s,roots)
    for e in s['evidence']:
        if e['id'] in affected and e['validity']!='historical': e['validity']='stale'
    reopen(s,affected);return sorted(affected)
def advance(s,old,new,base,reason):
    A={a['id']:a for a in s['artifacts']}
    if old not in s['active_artifact_ids'] or new in A: raise ValueError('advance requires active old and unique new revision')
    a=copy.deepcopy(A[old]);p=Path(a['path']);p=p if p.is_absolute() else Path(base)/p
    sha,size=digest(p)
    if (sha,size)==(a['sha256'],a['size']): raise ValueError('no artifact byte change')
    a.update(id=new,sha256=sha,size=size,parent_id=old,change=reason,changed_ranges=[],mapping_changed=None)
    s['artifacts'].append(a);s['active_artifact_ids']=[new if i==old else i for i in s['active_artifact_ids']]
    roots={e['id'] for e in s['evidence'] if old in e['artifact_ids']};affected=closure(s,roots)
    for e in s['evidence']:
        if e['id'] in roots: e['validity']='historical'
        elif e['id'] in affected and e['validity']!='historical': e['validity']='stale'
    reopen(s,affected);s['context']['durable']=False
    return sorted(affected)
def atomic_text(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f: f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        if os.name=='posix':
            dfd=os.open(path.parent,os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def mutate(path,expected,fn):
    path=Path(path);lock=path.with_name(path.name+'.lock')
    try: fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError: raise ValueError('writer lock exists; inspect owner before recovery')
    try:
        with os.fdopen(fd,'w') as f: f.write(str(os.getpid()))
        s=load(path);validate(s)
        if s['checkpoint_revision']!=expected: raise ValueError('checkpoint revision conflict')
        result=fn(s);s['checkpoint_revision']+=1;s['context']['durable']=True
        validate(s);atomic_text(path,json.dumps(s,indent=2,allow_nan=False)+'\n');return result
    finally: lock.unlink()
def budget(capacity,used,next_cost,future,margin,durable):
    vals=[capacity,used,next_cost,future,margin]
    if any(v is None for v in vals): return {'decision':'unknown-telemetry','action':'Use bounded output and checkpoint critical state; obtain actual host telemetry.'}
    if capacity<=0 or any(v<0 for v in vals) or used>capacity: raise ValueError('invalid budget inputs')
    h=capacity-used;required=next_cost+future+margin
    return {'headroom':h,'required':required,'decision':'continue' if h>=required else 'reduce-or-compact' if durable else 'checkpoint-first','action':'Compaction is host-controlled; reconsider after reducing the operation.' if h<required else 'Checkpoint independently at material changes.'}
def reset_context(s):
    """Invalidate session-specific measurements without rebinding target knowledge."""
    for key in ('capacity_tokens','used_tokens','next_cost_tokens','future_reserve_tokens','margin_tokens'):
        s['context'][key]=None
    s['context']['telemetry_current']=False
    return {'context_reset':True,'artifact_facts_preserved':True}
def loops(s):
    grouped={}
    for p in s['probes']:
        key=(tuple(sorted(p['artifact_ids'])),p['question_id'],p['capability'],p['scope'],p['signature'],p['recipe']['operation'],json.dumps(p['recipe']['parameters'],sort_keys=True,separators=(',',':')))
        grouped.setdefault(key,[]).append(p)
    return [{'question_id':k[1],'signature':k[4],'probes':[x['id'] for x in v],'action':'Review saturation; change discriminator or pursue another viable question.'} for k,v in grouped.items() if len(v)>=2 and all(x['novelty']=='none' for x in v[-2:])]
def views(s):
    n=s['next_probe'];qids=[q['id'] for q in s['questions'] if q['status']!='ANSWERED'][:5]
    q=next((q for q in s['questions'] if n and q['id']==n['question_id']),None)
    lines=['# CURRENT-STATE — generated',f"Checkpoint revision: {s['checkpoint_revision']}",'Canonical: INVESTIGATION.json',f"Objective: {s['objective']}",f"Active artifacts: {', '.join(s['active_artifact_ids'])}",f"Profiles: {', '.join(s['profiles'])}",f"Open questions (first five): {', '.join(qids)}",f"Active evidence IDs: {', '.join(q['evidence_ids']) if q else ''}",'NEXT: '+json.dumps(n,ensure_ascii=False),'Workflow caveats: '+json.dumps(s['workflow_notes'],ensure_ascii=False),'Noncurrent evidence count: '+str(sum(e['validity']!='current' for e in s['evidence']))]
    ledger=['# EVIDENCE-LEDGER — generated',f"Checkpoint revision: {s['checkpoint_revision']}",'Canonical: INVESTIGATION.json']
    for e in s['evidence']: ledger.extend(['','## '+e['id'],json.dumps(e,ensure_ascii=False,indent=2)])
    return '\n\n'.join(lines)+'\n','\n'.join(ledger)+'\n'
def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('validate');v.add_argument('state');v.add_argument('--verify-files',action='store_true')
    v=sub.add_parser('view');v.add_argument('state');v.add_argument('--out');v.add_argument('--ledger-out')
    v=sub.add_parser('loops');v.add_argument('state')
    v=sub.add_parser('invalidate');v.add_argument('state');v.add_argument('ids',nargs='+');v.add_argument('--expected-revision',type=int,required=True)
    v=sub.add_parser('advance');v.add_argument('state');v.add_argument('old');v.add_argument('new');v.add_argument('--expected-revision',type=int,required=True);v.add_argument('--reason',choices=['patch','replacement','rebuild'],required=True)
    v=sub.add_parser('reset-context');v.add_argument('state');v.add_argument('--expected-revision',type=int,required=True)
    v=sub.add_parser('budget')
    for name in ('capacity','used','next-cost','future','margin'): v.add_argument('--'+name,type=int)
    v.add_argument('--durable',action='store_true');args=parser.parse_args()
    try:
        if args.cmd=='budget': result=budget(args.capacity,args.used,args.next_cost,args.future,args.margin,args.durable)
        elif args.cmd=='invalidate': result={'affected':mutate(args.state,args.expected_revision,lambda s:invalidate(s,args.ids))}
        elif args.cmd=='advance': result={'revalidate':mutate(args.state,args.expected_revision,lambda s:advance(s,args.old,args.new,Path(args.state).resolve().parent,args.reason))}
        elif args.cmd=='reset-context': result=mutate(args.state,args.expected_revision,reset_context)
        else:
            s=load(args.state);validate(s,Path(args.state).resolve().parent,getattr(args,'verify_files',False))
            if args.cmd=='validate': result={'valid':True,'level':'schema-and-graph','active_file_bytes_verified':args.verify_files}
            elif args.cmd=='loops': result=loops(s)
            else:
                current,ledger=views(s)
                if args.out: atomic_text(args.out,current)
                if args.ledger_out: atomic_text(args.ledger_out,ledger)
                result={'view_generated':True,'checkpoint_revision':s['checkpoint_revision']}
                if not args.out and not args.ledger_out: print(current);return
        print(json.dumps(result,indent=2))
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'error':str(exc)}));raise SystemExit(1)
if __name__=='__main__': main()
