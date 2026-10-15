"""Compile design-time CVS JSON graph + runtime scenario into a portable contract.
No AI calls, no claims of validation; rejects broken source graph links.
"""
import json, hashlib, pathlib, copy, datetime, sys
ROOT=pathlib.Path(__file__).resolve().parent
ROLES=[
 ('sense','Signal Steward','read-only','Collect signals; inspect provenance and freshness'),
 ('context','Context Resolver','read-only','Join event against value graph and responsibilities'),
 ('value','Value Reasoner','recommend','Correlate evidence; estimate opportunity without claiming causality'),
 ('plan','Intervention Planner','recommend','Produce alternatives, assumptions and risk controls'),
 ('guard','Policy & Risk Gate','deterministic','Check tools, scope and approval conditions'),
 ('act','Action Broker','simulated-ticket','Draft non-operational work order after human approval'),
 ('verify','Outcome Auditor','read-only','Record post-action measurement as pending')]

def compile_pack(name):
 if name not in ('office','retail','manufacturing'): raise ValueError('Unrecognised pack')
 d=json.loads((ROOT/'data'/'design'/f'{name}.json').read_text())
 r=json.loads((ROOT/'data'/'scenarios'/f'{name}-runtime.json').read_text())
 assert r['enterprisePackRef']['packId']==d['packId'], 'Source pack mismatch'
 nodes={n['id']:n for n in d['nodes']}
 for e in d['edges']:
  if e['from'] not in nodes or e['to'] not in nodes: raise ValueError(f'Broken edge {e}')
 links=r['enterprisePackRef']['nodeIds']
 if any(n not in nodes for n in links): raise ValueError('Missing design-time node reference')
 # Bring connected graph back to the runtime, not only slides or flat signal strings.
 selected_edges=[e for e in d['edges'] if e['from'] in links or e['to'] in links]
 selected_ids=set(links)
 for e in selected_edges: selected_ids.update((e['from'],e['to']))
 subnodes=[copy.deepcopy(n) for n in d['nodes'] if n['id'] in selected_ids]
 objectives=[n for n in subnodes if n['type']=='board']
 hypotheses=[n for n in subnodes if n['type']=='hypothesis']
 metrics=[n for n in subnodes if n['type']=='metric']
 sources=[n for n in subnodes if n['type']=='source']
 agents=[{'id':a,'title':b,'authority':c,'purpose':purpose} for a,b,c,purpose in ROLES]
 created_at='2026-10-09' # versioned example, not real deployment timestamp
 manifest={
  'apiVersion':'cvs.openai.example/v1alpha1',
  'kind':'ValueIntentRuntime',
  'metadata':{'name':f'{name}-value-ops','version':'0.1.0','sourcePackId':d['packId'], 'sourceRuntimeId':r['packId'], 'status':'synthetic/unvalidated','compiledExampleDate':created_at},
  'valueIntent':{'boardObjectives':[{'id':n['id'],'name':n['title']} for n in objectives],
    'owner':r['valueIntent']['accountableOwner'], 'metric':r['valueIntent']['metric'],
    'baselineText':r['valueIntent']['baseline'],'targetText':r['valueIntent']['target'],
    'hypothesis':r['valueIntent']['benefitHypothesis'], 'valueStatus':'UNVALIDATED',
    'hypotheses':[{'id':n['id'],'name':n['title']} for n in hypotheses],
    'metricRefs':[{'id':n['id'],'name':n['title']} for n in metrics]},
  'evidence':{'sources':[{'id':n['id'],'name':n['title']} for n in sources],
    'snapshots':r['signalSnapshot'], 'provenance':'synthetic', 'confounders':['weather and occupancy mix','bookings, safety overrides','asset operating state'],
    'verification':'counterfactual required; no benefit certified'},
  'graph':{'nodes':subnodes,'edges':selected_edges,'primaryRefIds':links},
  'agentPlan':{'strategy':'coordinator-with-role-handlers','agents':agents,
    'flow':['sense','context','value','plan','guard','human-approval','act','verify']},
  'governance':{'mode':'SHADOW','minimumEvidence':'customer-verified before financial claim',
    'approval':{'required':True,'role':r['valueIntent']['approvalAuthority']},
    'allowedActions':['read_synthetic_events','reason_on_graph','draft_work_order'],
    'deniedActions':['bms.setpoint.write','plc.write','access_control.write','production.system.write'],
    'riskBoundary':r['valueIntent']['riskBoundary'],
    'externalSystemsEnabled':False},
  'commercial':{'partnerRole':r.get('partnerRole'), 'ciscoCapabilityPositioning':r.get('ciscoRole'),
    'noRevenueOrROIClaimsWithoutMeasuredEvidence':True},
  'runtime':{'eventSource':'embedded-synthetic-snapshot','eventTimeoutSeconds':15,
    'idempotencyRequired':True,'auditRequired':True,'outcomeState':'NOT_MEASURED'},
  'presentation':{'title':r['title'],'subtitle':r['subtitle'],'scene':r['scene'], 'industry':r['industry']}
 }
 payload=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
 manifest['metadata']['sha256']=hashlib.sha256(payload).hexdigest()
 return manifest

def write_all():
 for n in ('office','retail','manufacturing'):
  x=compile_pack(n)
  (ROOT/'manifests'/f'{n}.json').write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
  print(f'{n}: {len(x["graph"]["nodes"])} connected nodes; {len(x["graph"]["edges"])} edges; hash {x["metadata"]["sha256"][:12]}')
if __name__=='__main__': write_all()
