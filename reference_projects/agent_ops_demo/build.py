import json,base64
from pathlib import Path
r=Path(__file__).parent
packs=[json.loads((r/'packs'/f'{p}-runtime.json').read_text()) for p in ('office','retail','manufacturing')]
imgs={p:'data:image/webp;base64,'+base64.b64encode((r/'assets'/f'{p}.webp').read_bytes()).decode() for p in ('office','retail','manufacturing')}
h=(r/'index_template.html').read_text()
h=h.replace('const BUILTIN_PACKS=__PACK_DATA__','const BUILTIN_PACKS='+json.dumps(packs,ensure_ascii=False,separators=(',',':'))).replace('const IMAGES=__IMAGES__','const IMAGES='+json.dumps(imgs,separators=(',',':')))
h=h.replace('<script src="__APPJS__"></script>','<script>\n'+(r/'app.js').read_text()+'\n</script>')
(r/'index.html').write_text(h)
Path('/mnt/data/Agentic_Value_Operations_Live_Demonstrator.html').write_text(h)
print('Built standalone bytes:',len(h.encode()),'Scenarios:',[p['title'] for p in packs])
