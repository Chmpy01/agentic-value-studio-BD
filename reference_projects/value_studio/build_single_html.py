import base64,json
from pathlib import Path
r=Path(__file__).resolve().parent
packs=[json.loads((r/'packs'/f'{x}.json').read_text()) for x in ('office','retail','manufacturing')]
art={x:'data:image/webp;base64,'+base64.b64encode((r/'assets'/f'{x}.webp').read_bytes()).decode() for x in ('office','retail','manufacturing')}
t=(r/'index_template.html').read_text()
html=t.replace('__PACKS__',json.dumps(packs,ensure_ascii=False).replace('<','\\u003c')).replace('__ART__',json.dumps(art))
(r/'index.html').write_text(html)
print('Built offline app',str(r/'index.html'),len(html),'chars')
