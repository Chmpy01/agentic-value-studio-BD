"""Localhost-only zero dependency API + UI for the Value Twin runtime."""
import json,urllib.parse,http.server,threading,pathlib,mimetypes,os
import engine
ROOT=pathlib.Path(__file__).resolve().parent
engine.init()

class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):return
 def response(self,obj,status=200):
  payload=json.dumps(obj,ensure_ascii=False).encode()
  self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
 def do_GET(self):
  url=urllib.parse.urlparse(self.path); path=url.path; qs=urllib.parse.parse_qs(url.query)
  if path=='/api/health':return self.response({'ok':True,'mode':'SHADOW','liveConnectors':False})
  if path=='/api/packs':return self.response([{'id':n,'title':engine.manifest(n)['presentation']['title']} for n in sorted(engine.SCENARIOS)])
  if path=='/api/manifest':
   try:return self.response(engine.manifest(qs.get('pack',['office'])[0]))
   except Exception as exc:return self.response({'error':str(exc)},400)
  if path.startswith('/api/runs/'):
   rid=path[len('/api/runs/'):]; run=engine.get_run(rid)
   return self.response(run) if run else self.response({'error':'Not found'},404)
  if path=='/' or path=='/index.html':
   payload=(ROOT/'static'/'index.html').read_bytes()
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
  if path.startswith('/static/'):
   p=(ROOT/path.lstrip('/')).resolve()
   if ROOT/'static' not in p.parents or not p.is_file():return self.response({'error':'Not found'},404)
   payload=p.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(p))[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
  self.response({'error':'Not found'},404)
 def do_POST(self):
  length=int(self.headers.get('Content-Length','0'))
  if length>20000:return self.response({'error':'Payload too large'},413)
  try: obj=json.loads(self.rfile.read(length).decode()) if length else {}
  except Exception:return self.response({'error':'Invalid JSON'},400)
  if self.path=='/api/runs':
   try:rid=engine.start(obj.get('pack','office'));return self.response({'runId':rid},201)
   except Exception as exc:return self.response({'error':str(exc)},400)
  if self.path.startswith('/api/runs/') and self.path.endswith('/approval'):
   rid=self.path[len('/api/runs/'):-len('/approval')].strip('/')
   try:return self.response(engine.decide(rid,obj.get('decision')))
   except KeyError:return self.response({'error':'Not found'},404)
   except Exception as exc:return self.response({'error':str(exc)},409)
  self.response({'error':'Not found'},404)

if __name__=='__main__':
 print('Cognitive Value Agentic Runtime | local shadow mode | http://127.0.0.1:8876',flush=True)
 http.server.ThreadingHTTPServer((os.environ.get('BIND_HOST','127.0.0.1'),int(os.environ.get('PORT','8876'))),Handler).serve_forever()
