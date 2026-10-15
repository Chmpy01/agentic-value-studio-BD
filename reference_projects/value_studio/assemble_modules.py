"""Recompose design-time graph modules into the single runtime JSON document."""
import json,pathlib,sys
R=pathlib.Path(__file__).parent
key=sys.argv[1] if len(sys.argv)>1 else 'office'
folder=R/'modules'/key
mods=[json.loads(p.read_text()) for p in sorted(folder.glob('*.json'))]
if len(mods)!=7:raise SystemExit(f'Expected 7 modules, got {len(mods)}')
if len({m['packId'] for m in mods})!=1:raise SystemExit('Mixed pack IDs are not allowed')
pack={'nodes':[],'edges':[]}
for m in mods:
 payload=m['payload']
 for k,v in payload.items():
  if k in ('nodes','edges'):pack[k].extend(v)
  elif k in pack:raise ValueError(f'Duplicate top-level property: {k}')
  else:pack[k]=v
out=R/'packs'/(key+'_assembled.json')
out.write_text(json.dumps(pack,indent=2,ensure_ascii=False))
print('Written:',out, 'nodes',len(pack['nodes']),'edges',len(pack['edges']))
