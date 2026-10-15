#!/usr/bin/env python3
"""Offline pack/schema/graph integrity check. jsonschema optional."""
import json
from pathlib import Path
r=Path(__file__).resolve().parent
schema=json.loads((r/'schemas/cvs-pack.schema.json').read_text())
try:
 from jsonschema import Draft202012Validator
 val=Draft202012Validator(schema)
except ImportError:val=None
fails=0
for path in sorted((r/'packs').glob('*.json')):
 if path.stem.endswith('_assembled'):continue
 p=json.loads(path.read_text());ids=[n['id'] for n in p.get('nodes',[])];seen=set(ids);err=[]
 if len(seen)!=len(ids):err.append('duplicate nodes')
 for edge in p['edges']:
  if edge['from'] not in seen or edge['to'] not in seen:err.append('bad edge')
 for sc in p['story']:
  for x in sc.get('focusNodeIds',[]):
   if x not in seen:err.append('bad scene focus '+x)
 for x in p.get('evidenceRegister',[]):
  if x['nodeId'] not in seen:err.append('bad evidence '+x['nodeId'])
 for hot in p.get('scene',{}).get('hotspots',[]):
  if hot['nodeId'] not in seen:err.append('bad hotspot')
 if val:err.extend(e.message for e in val.iter_errors(p))
 print(path.stem.upper(), 'PASS' if not err else 'FAIL',len(p['nodes']),'nodes',len(p['edges']),'edges',len(p['story']),'scenes',len(p.get('evidenceRegister',[])),'evidence records')
 if err:
  fails+=1
  for e in err[:8]:print('  -',e)
if not val:print('Note: install jsonschema for full schema validation (graph links checked regardless).')
raise SystemExit(1 if fails else 0)
