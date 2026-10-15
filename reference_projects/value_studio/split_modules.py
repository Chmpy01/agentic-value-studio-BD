import json,pathlib
R=pathlib.Path(__file__).resolve().parent
for path in (R/'packs').glob('*.json'):
 p=json.loads(path.read_text());d=R/'modules'/p['packId'];d.mkdir(parents=True,exist_ok=True)
 def save(moduleId,payload):
  obj={'moduleType':'cvs-module','schemaVersion':'1.0.0','packId':p['packId'],'moduleId':moduleId,'payload':payload}
  (d/(moduleId+'.json')).write_text(json.dumps(obj,indent=2,ensure_ascii=False))
 meta=['schemaVersion','packId','name','industry','subtitle','customer','status','provenance','outcomeTags','validation']
 save('01_manifest',{k:p[k] for k in meta})
 buckets={'02_enterprise':['board','function','persona','stream'],'03_signals':['source','signal'],'04_value':['hypothesis','metric','risk'],'05_ecosystem':['capability','partner','offer']}
 for module,types in buckets.items():save(module,{'nodes':[n for n in p['nodes'] if n['type'] in types]})
 save('06_relations',{'edges':p['edges']})
 save('07_presentation',{k:p[k] for k in ['navigation','lenses','story','tracks','scene','theme','ui','evidenceRegister']})
 print('modularised',p['packId'],'7 JSON modules')
