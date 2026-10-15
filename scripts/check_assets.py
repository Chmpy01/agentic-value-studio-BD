#!/usr/bin/env python3
"""Standard library preflight for Cursor handoff files. No network or credentials."""
import json, pathlib, sys
r=pathlib.Path(__file__).resolve().parents[1]
paths={
  "office pack":r/"reference_projects/value_studio/packs/office.json",
  "retail pack":r/"reference_projects/value_studio/packs/retail.json",
  "manufacturing pack":r/"reference_projects/value_studio/packs/manufacturing.json",
  "office intent":r/"reference_projects/agent_runtime/manifests/office.json",
  "runtime compiler":r/"reference_projects/agent_runtime/compiler.py",
  "agent ops workflow":r/"reference_projects/agent_ops_demo/packs/office-runtime.json",
  "3D office":r/"reference_projects/3d_library/assets/smart_office.glb",
  "graph schema":r/"reference_projects/value_studio/schemas/cvs-pack.schema.json",
  "Cursor prompt":r/"MASTER_CURSOR_PROMPT.md",
}
errors=[]
for label,path in paths.items():
 if not path.is_file():errors.append(f"MISSING {label}: {path}")
 else:print(f"OK {label}: {path.relative_to(r)}")
for n in ('office','retail','manufacturing'):
 f=r/f'reference_projects/value_studio/packs/{n}.json'
 if not f.is_file():continue
 d=json.loads(f.read_text());ids={x['id'] for x in d['nodes']}
 for e in d['edges']:
  if e['from'] not in ids or e['to'] not in ids:errors.append(f'{n} invalid edge: {e}')
 print(f'{n}: {len(ids)} graph nodes, {len(d["edges"])} edges, {len(d["story"])} story scenes')
for n in ('office','retail','manufacturing'):
 p=r/f'reference_projects/agent_runtime/manifests/{n}.json'
 if p.is_file():
  d=json.loads(p.read_text())
  if d.get('governance',{}).get('externalSystemsEnabled') is not False:errors.append(f'{n} unsafe externalSystemsEnabled')
  if d.get('runtime',{}).get('outcomeState')!='NOT_MEASURED':errors.append(f'{n} unsafe outcomeState')
print('PASS preflight' if not errors else '\n'.join(errors))
sys.exit(bool(errors))
