"""Local durable-ish SQLite demo: replayable agent handoffs, approval gate.
Not production durable execution: use LangGraph persistent checkpointer/Temporal for that.
"""
from __future__ import annotations
import sqlite3,json,uuid,time,threading,pathlib,datetime
from contextlib import contextmanager
from agents import HANDLERS
ROOT=pathlib.Path(__file__).resolve().parent
DB=ROOT/'state'/'runs.sqlite3'
SCENARIOS={'office','retail','manufacturing'}
_LOCK=threading.RLock()

@contextmanager
def connect():
 c=sqlite3.connect(str(DB),timeout=5);c.row_factory=sqlite3.Row
 try:
  with c: yield c
 finally: c.close()

def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connect() as c:
  c.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, pack TEXT, state TEXT, approval TEXT, created TEXT, updated TEXT)')
  c.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, agent TEXT, stage TEXT, message TEXT, details TEXT, created TEXT)')

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

def emit(runid,agent,stage,message,details):
 with _LOCK,connect() as c:
  c.execute('INSERT INTO events (run_id,agent,stage,message,details,created) VALUES (?,?,?,?,?,?)',(runid,agent,stage,message,json.dumps(details,ensure_ascii=False),utc()))
  c.execute('UPDATE runs SET updated=? WHERE id=?',(utc(),runid))

def state(runid,value):
 with _LOCK,connect() as c:c.execute('UPDATE runs SET state=?,updated=? WHERE id=?',(value,utc(),runid))

def get_run(runid):
 with connect() as c:
  row=c.execute('SELECT * FROM runs WHERE id=?',(runid,)).fetchone()
  if not row: return None
  ev=[dict(x) for x in c.execute('SELECT * FROM events WHERE run_id=? ORDER BY seq',(runid,))]
 for e in ev:e['details']=json.loads(e['details'])
 return {'run':dict(row),'events':ev}

def start(pack):
 if pack not in SCENARIOS:raise ValueError('Unknown scenario')
 runid=str(uuid.uuid4())
 with _LOCK,connect() as c:
  c.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)',(runid,pack,'RUNNING',None,utc(),utc()))
 threading.Thread(target=process,args=(runid,'pre'),daemon=True).start()
 return runid

def manifest(pack):
 if pack not in SCENARIOS: raise ValueError('Unknown scenario')
 return json.loads((ROOT/'manifests'/f'{pack}.json').read_text())

def process(runid,phase):
 try:
  x=get_run(runid)
  if not x:return
  m=manifest(x['run']['pack']); s={'runId':runid}
  stages=['sense','context','value','plan','guard'] if phase=='pre' else ['act','verify']
  for role in stages:
   if phase=='post' and get_run(runid)['run']['approval']!='approved':return
   result=HANDLERS[role](m,s)
   emit(runid,role,'complete',result['name'],result)
   if role=='guard' and not result['passed']:
    emit(runid,'guard','blocked','Unsafe contract — policy gate refused execution',{});state(runid,'BLOCKED');return
   time.sleep(0.28)
  if phase=='pre':
   emit(runid,'human','approval-needed','Awaiting FM / operations approval; no tool writes allowed',{'authority':m['governance']['approval']['role'],'approvedActions':m['governance']['allowedActions']})
   state(runid,'AWAITING_APPROVAL')
  else:
   state(runid,'COMPLETE_NOT_MEASURED')
 except Exception as exc:
  emit(runid,'system','error','Workflow error',{'type':type(exc).__name__,'message':str(exc)})
  state(runid,'ERROR')

def decide(runid,decision):
 if decision not in ('approved','rejected'):raise ValueError('Invalid decision')
 with _LOCK,connect() as c:
  row=c.execute('SELECT * FROM runs WHERE id=?',(runid,)).fetchone()
  if not row: raise KeyError(runid)
  if row['state']!='AWAITING_APPROVAL':raise ValueError('Run not awaiting approval')
  # One-time atomic decision; future retries cannot bypass the gate.
  changed=c.execute("UPDATE runs SET state=?, approval=?,updated=? WHERE id=? AND state='AWAITING_APPROVAL'",('RUNNING' if decision=='approved' else 'REJECTED',decision,utc(),runid)).rowcount
  if changed!=1:raise ValueError('Approval already handled')
 emit(runid,'human','decision', 'Approved simulated work-order draft' if decision=='approved' else 'Rejected: no action',{'decision':decision,'externalSystemWrite':False})
 if decision=='approved':threading.Thread(target=process,args=(runid,'post'),daemon=True).start()
 return get_run(runid)
