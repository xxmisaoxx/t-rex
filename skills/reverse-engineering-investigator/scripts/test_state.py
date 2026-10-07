#!/usr/bin/env python3
"""Mechanical state tests, separate from agent behavior evaluations."""
import copy,json,tempfile,unittest
from pathlib import Path
from re_state import ROOT,validate,load,digest,invalidate,advance,mutate,views,budget,loops,atomic_text
def fixture(path):
    s=json.loads((ROOT/'templates/INVESTIGATION.json').read_text())
    path.write_bytes(b'current test bytes');sha,size=digest(path)
    s['objective']='Locate a value source';s['profiles']=['windows-pe']
    s['artifacts']=[{'id':'R1','path':str(path),'sha256':sha,'size':size,'format':'PE','architecture':'x64','parent_id':None,'change':'initial','changed_ranges':[],'mapping_changed':False}]
    s['active_artifact_ids']=['R1'];s['questions']=[{'id':'Q1','text':'Where is the value initialized?','status':'UNRESOLVED','evidence_ids':['E1']}]
    recipe={'capability':'byte-read','provider':None,'operation':'read','parameters':{'offset':4,'size':8},'output_path':None}
    e={'id':'E1','class':'OBSERVED','claim':'Provider reports these bytes','artifact_ids':['R1'],'dependencies':[],'confidence':'HIGH','validity':'current','location':{'domain':'raw','value':'0x4','member':None},'coverage':'complete','search_boundary':'8 bytes from raw 4','limits':'Fixture bytes only','recipe':recipe,'runtime':None,'supersedes':[]}
    s['evidence']=[e];s['next_probe']={'question_id':'Q1','artifact_ids':['R1'],'capability':'disassembly','operation':'decode','parameters':{'rva':'0x1100'},'scope':'one block','discriminator':'Identify value reaching store','fallback':'read relocation metadata'}
    s['context']['durable']=True;return s
class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.d=Path(self.temp.name);self.binary=self.d/'target.bin';self.s=fixture(self.binary);self.path=self.d/'INVESTIGATION.json';atomic_text(self.path,json.dumps(self.s))
    def tearDown(self): self.temp.cleanup()
    def rejected(self,s):
        with self.assertRaises(ValueError):validate(s)
    def derived(self,ident='E2',dep='E1'):
        e=copy.deepcopy(self.s['evidence'][0]);e.update(id=ident,**{'class':'DERIVED','dependencies':[dep]});self.s['evidence'].append(e);return e
    def test_empty_template(self): validate(json.loads((ROOT/'templates/INVESTIGATION.json').read_text()))
    def test_valid_and_verify_bytes(self): self.assertTrue(validate(self.s,self.d,True))
    def test_duplicate_id(self): self.s['evidence'].append(copy.deepcopy(self.s['evidence'][0]));self.rejected(self.s)
    def test_duplicate_json_key(self):
        self.path.write_text('{"schema_version":"3.0","schema_version":"2.1"}')
        with self.assertRaises(ValueError):load(self.path)
    def test_nonstandard_json_number(self):
        self.path.write_text('{"value":NaN}')
        with self.assertRaises(ValueError):load(self.path)
    def test_dangling_dep(self): self.derived(dep='E404');self.rejected(self.s)
    def test_dependency_cycle(self): self.derived();self.s['evidence'][0]['dependencies']=['E2'];self.rejected(self.s)
    def test_supersession_cycle(self): self.derived();self.s['evidence'][0]['supersedes']=['E2'];self.s['evidence'][1]['supersedes']=['E1'];self.rejected(self.s)
    def test_lineage_cycle(self): self.s['artifacts'][0]['parent_id']='R1';self.rejected(self.s)
    def test_derived_without_support(self): self.s['evidence'][0]['class']='DERIVED';self.rejected(self.s)
    def test_current_on_inactive(self): self.s['active_artifact_ids']=[];self.rejected(self.s)
    def test_current_dep_stale(self): self.derived();self.s['evidence'][0]['validity']='stale';self.rejected(self.s)
    def test_runtime_requires_boundary(self): self.s['evidence'][0]['location']['domain']='runtime-va';self.rejected(self.s)
    def test_invalid_next_question(self): self.s['next_probe']['question_id']='Q404';self.rejected(self.s)
    def test_next_answered(self): self.s['questions'][0]['status']='ANSWERED';self.rejected(self.s)
    def test_answered_without_evidence(self): self.s['next_probe']=None;self.s['questions'][0].update(status='ANSWERED',evidence_ids=[]);self.rejected(self.s)
    def test_unsupported_hypothesis_status(self): self.s['hypotheses']=[{'id':'H1','question_id':'Q1','text':'x','status':'REJECTED','evidence_ids':[]}];self.rejected(self.s)
    def test_unknown_profile(self): self.s['profiles']=['made-up'];self.rejected(self.s)
    def test_invalid_range(self): self.s['artifacts'][0]['changed_ranges']=[{'domain':'raw','start':8,'end':8}];self.rejected(self.s)
    def test_wrong_schema_and_extra(self): self.s['unexpected']='x';self.rejected(self.s)
    def test_drift(self):
        self.binary.write_bytes(b'replacement bytes')
        with self.assertRaises(ValueError):validate(self.s,self.d,True)
    def test_transitive_invalidation_and_reopen(self):
        self.derived();self.derived('E3','E2');self.s['questions'][0].update(status='ANSWERED',evidence_ids=['E3']);self.s['next_probe']=None
        self.s['hypotheses']=[{'id':'H1','question_id':'Q1','text':'x','status':'REJECTED','evidence_ids':['E2']}]
        self.assertEqual(invalidate(self.s,['E1']),['E1','E2','E3']);self.assertEqual(self.s['questions'][0]['status'],'PARTIAL');self.assertEqual(self.s['hypotheses'][0]['status'],'UNTESTED');validate(self.s)
    def test_selective_unrelated(self):
        e=copy.deepcopy(self.s['evidence'][0]);e['id']='E9';self.s['evidence'].append(e)
        invalidate(self.s,['E1']);self.assertEqual(e['validity'],'current');validate(self.s)
    def test_unknown_invalidation_root(self):
        with self.assertRaises(ValueError):invalidate(self.s,['E404'])
    def test_advance_preserves_other_artifact(self):
        other=self.d/'other.bin';other.write_bytes(b'other');sha,size=digest(other);a=copy.deepcopy(self.s['artifacts'][0]);a.update(id='R9',path=str(other),sha256=sha,size=size);self.s['artifacts'].append(a);self.s['active_artifact_ids'].append('R9')
        e=self.derived();e['artifact_ids']=['R9'];u=copy.deepcopy(self.s['evidence'][0]);u.update(id='E9',artifact_ids=['R9']);self.s['evidence'].append(u)
        self.binary.write_bytes(b'patched');advance(self.s,'R1','R2',self.d,'patch')
        self.assertEqual(self.s['evidence'][0]['validity'],'historical');self.assertEqual(e['validity'],'stale');self.assertEqual(u['validity'],'current');self.assertIsNone(self.s['next_probe']);self.assertEqual(self.s['artifacts'][-1]['parent_id'],'R1');self.assertIsNone(self.s['artifacts'][-1]['mapping_changed']);validate(self.s,self.d,True)
    def test_advance_no_change(self):
        with self.assertRaises(ValueError):advance(self.s,'R1','R2',self.d,'replacement')
    def test_atomic_mutation(self):
        result=mutate(self.path,0,lambda s:invalidate(s,['E1']));after=load(self.path)
        self.assertEqual(result,['E1']);self.assertEqual(after['checkpoint_revision'],1);self.assertEqual(after['evidence'][0]['validity'],'stale');self.assertFalse(self.path.with_name(self.path.name+'.lock').exists())
    def test_revision_conflict_preserves_bytes(self):
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mutate(self.path,3,lambda s:invalidate(s,['E1']))
        self.assertEqual(before,self.path.read_bytes())
    def test_writer_lock_preserves(self):
        lock=self.path.with_name(self.path.name+'.lock');lock.write_text('owner')
        with self.assertRaises(ValueError):mutate(self.path,0,lambda s:None)
        self.assertEqual(lock.read_text(),'owner')
    def test_invalid_mutation_preserves_bytes(self):
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mutate(self.path,0,lambda s:s.update(active_artifact_ids=[]))
        self.assertEqual(before,self.path.read_bytes())
    def test_budget_1m(self): self.assertEqual(budget(1000000,780000,12000,25000,20000,True)['decision'],'continue')
    def test_budget_small_unpersisted(self): self.assertEqual(budget(32000,30000,3000,1000,2000,False)['decision'],'checkpoint-first')
    def test_budget_small_persisted(self): self.assertEqual(budget(32000,30000,3000,1000,2000,True)['decision'],'reduce-or-compact')
    def test_budget_unknown(self): self.assertEqual(budget(None,None,1,1,1,False)['decision'],'unknown-telemetry')
    def test_budget_invalid(self):
        with self.assertRaises(ValueError):budget(10,11,1,1,1,True)
    def test_view_revision(self):
        current,ledger=views(self.s);self.assertIn('Checkpoint revision: 0',current);self.assertIn('Identify value reaching store',current);self.assertIn('E1',ledger)
    def test_loop_advisory_and_changed_parameters(self):
        p={'id':'P1','question_id':'Q1','artifact_ids':['R1'],'signature':'R1-Q1-decode-block','capability':'decode','scope':'block','outcome':'completed','novelty':'none','retry_condition':'changed input','recipe':copy.deepcopy(self.s['evidence'][0]['recipe'])}
        p2=copy.deepcopy(p);p2['id']='P2';self.s['probes']=[p,p2];self.assertEqual(len(loops(self.s)),1)
        p2['recipe']['parameters']['offset']=9;self.assertEqual(loops(self.s),[])
    def test_long_dependency_chain(self):
        prev='E1'
        for i in range(2,1202): self.derived('E'+str(i),prev);prev='E'+str(i)
        validate(self.s);self.assertEqual(len(invalidate(self.s,['E1'])),1201);validate(self.s)
    def test_unsupported_schema_keyword_fails_closed(self):
        from schema_check import check
        with self.assertRaises(ValueError):check(1,{'type':'integer','madeUpConstraint':True})
if __name__=='__main__':unittest.main(verbosity=2)
