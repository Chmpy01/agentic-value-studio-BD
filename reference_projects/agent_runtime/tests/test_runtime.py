import sys, pathlib, unittest,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import compiler,agents,engine
class ContractTests(unittest.TestCase):
 def test_all_three_manifests(self):
  for n in ('office','retail','manufacturing'):
   m=compiler.compile_pack(n)
   self.assertEqual(len(m['agentPlan']['agents']),7)
   self.assertTrue(m['graph']['nodes'])
   self.assertTrue(m['graph']['edges'])
   self.assertEqual(m['governance']['mode'],'SHADOW')
   self.assertFalse(m['governance']['externalSystemsEnabled'])
   self.assertEqual(m['valueIntent']['valueStatus'],'UNVALIDATED')
 def test_guard_refuses_physical_writes(self):
  m=compiler.compile_pack('office'); self.assertTrue(agents.guard(m,{})['passed'])
  m['governance']['externalSystemsEnabled']=True
  self.assertFalse(agents.guard(m,{})['passed'])
 def test_workflow_pause_reject_and_approve(self):
  engine.init()
  for decision in ('rejected','approved'):
   rid=engine.start('office')
   for _ in range(55):
    s=engine.get_run(rid)['run']['state']
    if s=='AWAITING_APPROVAL':break
    time.sleep(.06)
   self.assertEqual(s,'AWAITING_APPROVAL')
   result=engine.decide(rid,decision)
   if decision=='rejected':
    self.assertEqual(result['run']['state'],'REJECTED')
    self.assertFalse(any(x['agent']=='act' for x in result['events']))
   else:
    for _ in range(40):
     result=engine.get_run(rid)
     if result['run']['state']=='COMPLETE_NOT_MEASURED':break
     time.sleep(.06)
    self.assertEqual(result['run']['state'],'COMPLETE_NOT_MEASURED')
    step=[x for x in result['events'] if x['agent']=='act'][0]
    self.assertFalse(step['details']['externalSystemWritten'])
    aud=[x for x in result['events'] if x['agent']=='verify'][0]
    self.assertIsNone(aud['details']['realisedValue'])
if __name__=='__main__':unittest.main()
