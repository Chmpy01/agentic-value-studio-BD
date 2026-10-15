"""Optional REAL LangGraph state-machine demonstration, using bounded deterministic roles.
Requires: pip install langgraph (API tested against official interrupt/Command pattern)
This does NOT create LLM agents or connect to AGNTCY; intended as an orchestration swap-in.
"""
from __future__ import annotations
import sys,pathlib,uuid,typing
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from compiler import compile_pack
from agents import HANDLERS
from langgraph.graph import StateGraph,START,END
from langgraph.types import interrupt,Command
from langgraph.checkpoint.memory import InMemorySaver

class State(typing.TypedDict,total=False):
    manifest: dict
    runId: str
    results: dict
    approved: bool

def role_node(name):
    def apply(state:State):
        result=HANDLERS[name](state['manifest'],state)
        if name=='guard' and not result.get('passed',False):
            raise RuntimeError('Policy gate rejected this manifest')
        return {'results':{**state.get('results',{}),name:result}}
    return apply

def approval(state:State):
    response=interrupt({'request':'Approve simulated work-order draft only',
                        'action':'draft_work_order','externalSystemsEnabled':False,
                        'approver':state['manifest']['governance']['approval']['role']})
    return {'approved':response is True}

def route(state:State):return 'act' if state.get('approved') else END

def build():
    builder=StateGraph(State)
    for name in ['sense','context','value','plan','guard','act','verify']:
        builder.add_node(name,role_node(name))
    builder.add_node('human_approval',approval)
    builder.add_edge(START,'sense')
    for src,dst in [('sense','context'),('context','value'),('value','plan'),('plan','guard'),('guard','human_approval'),('act','verify')]:builder.add_edge(src,dst)
    builder.add_conditional_edges('human_approval',route)
    builder.add_edge('verify',END)
    return builder.compile(checkpointer=InMemorySaver())

if __name__=='__main__':
    pack=sys.argv[1] if len(sys.argv)>1 else 'office'
    graph=build(); config={'configurable':{'thread_id':str(uuid.uuid4())}}
    first=graph.invoke({'manifest':compile_pack(pack),'runId':str(uuid.uuid4()),'results':{}},config)
    if '__interrupt__' in first:
        print('PAUSED FOR HUMAN REVIEW:',first['__interrupt__'])
        ans=input('Approve a SIMULATED work-order draft (y/N)? ').strip().lower()=='y'
        result=graph.invoke(Command(resume=ans),config)
    else:result=first
    print('FINISHED. APPROVED:',result.get('approved'))
    print('AGENTS RUN:',list(result.get('results',{})))
    print('MEASURED VALUE:',result.get('results',{}).get('verify',{}).get('realisedValue'))
