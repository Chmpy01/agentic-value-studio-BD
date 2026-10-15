"""Bounded logical agents. All decisions deterministic or explicitly marked suggested.
Swap role handlers for LangGraph/A2A agents after pilot security approval.
"""
from datetime import datetime,timezone

def sense(m,s):
 snapshots=m['evidence']['snapshots']
 return {'name':'Normalised signals','status':'SIMULATED','readings':[{'source':x['source'],'name':x['name'],'value':x['value'],'quality':x.get('quality','unknown')} for x in snapshots], 'assertion':'These are synthetic observations, not a live Cisco/BMS connection.'}

def context(m,s):
 return {'name':'Value graph context','sourcePack':m['metadata']['sourcePackId'], 'linkedNodes':[x['id'] for x in m['graph']['nodes']], 'boardPriorities':m['valueIntent']['boardObjectives'],'owner':m['valueIntent']['owner'], 'evidenceState':'illustrative'}

def value(m,s):
 return {'name':'Hypothesis evaluation','hypothesis':m['valueIntent']['hypothesis'],'metric':m['valueIntent']['metric'],'baseline':m['valueIntent']['baselineText'],'target':m['valueIntent']['targetText'],'confidence':'UNVALIDATED', 'counterfactualNeeded':True,'certifiedBenefit':None}

def plan(m,s):
 scen=m['presentation']['scene']; opts={
  'office':['Review occupied hours versus HVAC schedule','Check IEQ and accessibility overrides','Propose FM schedule review work order'],
  'retail':['Review refrigeration exception with store duty manager','Check product temperature limits','Draft inspection work order'],
  'manufacturing':['Review machine micro-stop events with plant operations','Check production scheduling and safety','Draft maintenance analysis work order']}
 return {'name':'Bounded intervention options','options':opts.get(scen,['Review and create a work order']),'physicalCommands':False,'sideEffectsToCheck':['comfort/safety','operational continuity','data confidentiality']}

def guard(m,s):
 p=m['governance']; allowed=set(p['allowedActions']); forbidden=set(p['deniedActions'])
 safe=(p['mode']=='SHADOW' and not p['externalSystemsEnabled'] and 'draft_work_order' in allowed and len(forbidden)>=1 and p['approval']['required'])
 return {'name':'Deterministic policy gate','passed':safe,'mode':p['mode'],'approvalRequired':True,'approverRole':p['approval']['role'],'blockedCommands':sorted(forbidden),'canExecutePhysicalControls':False}

def act(m,s):
 return {'name':'Work-order draft (no external write)','ticketType':'SIMULATED_WORK_ORDER','idempotencyKey':s['runId']+':work-order','status':'DRAFTED_ONLY','externalSystemWritten':False,'actionSummary':'Request human-led operational review for '+m['presentation']['title']}

def verify(m,s):
 return {'name':'Independent outcome ledger','verificationState':'NOT_MEASURED','realisedValue':None,'measurementStatus':'AWAITING_REAL_BASELINE_AND_OBSERVATION','nextAction':'Gather before/after outcome evidence with controls and an agreed measurement period','attribution':'NOT_ESTABLISHED'}

HANDLERS={'sense':sense,'context':context,'value':value,'plan':plan,'guard':guard,'act':act,'verify':verify}
