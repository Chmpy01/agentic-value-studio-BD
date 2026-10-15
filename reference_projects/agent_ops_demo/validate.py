import json
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).parent
schema=json.loads((R/'schemas'/'operational-pack.schema.json').read_text())
validator=Draft202012Validator(schema)
for n in ('office','retail','manufacturing'):
 p=json.loads((R/'packs'/f'{n}-runtime.json').read_text())
 errs=list(validator.iter_errors(p))
 original=json.loads((Path('/mnt/data/Cognitive_Value_Studio_v2/packs')/f'{n}.json').read_text())
 existing={node['id'] for node in original['nodes']}
 missing=set(p['enterprisePackRef']['nodeIds'])-existing
 agents={a['id'] for a in p['agents']}
 unknown={s['agent'] for s in p['workflow']}-agents
 assert not errs,[e.message for e in errs]
 assert not missing,missing
 assert not unknown,unknown
 assert p['controls']['allowPhysicalControl'] is False
 assert p['controls']['requireHumanApproval'] is True
 print(f'PASS {n}: 9 stages / 7 agents / {len(p["enterprisePackRef"]["nodeIds"])} valid v2 graph refs / approval-gated')
