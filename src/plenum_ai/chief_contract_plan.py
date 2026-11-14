"""Compose existing PUBLIC specialist contracts through the original Chief.

One existing local ChatOllama structured-output choice; immutable plan and
original SHA checkpoints. No new framework, arbitrary tools, account scope,
paid model, or automatic acceptance of an unrestricted founder objective.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
import os
import math
from pathlib import Path
import re

from .chief_workforce_command import CHIEF_MAGIC, CHIEF_TITLE, MODEL, MODEL_URL, parse_founder_chief
from .chief_domain_transfer import read_crossref
from .mission_checkpoint import artifact_digest, load_checkpoint, save_checkpoint, verified_previous_result, objective_digest

MAGIC = 'PLENUM_CHIEF_PUBLIC_CONTRACT_MISSION_V1'
DOI_RE = re.compile(r'(?<![\w/])(10\.[0-9]{4,9}/[A-Za-z0-9][A-Za-z0-9.()/_+-]{0,100})(?![\w/])')
TOOLS = {'noaa_metadata':'research-specialist','station_validation':'coding-specialist',
         'crossref_metadata':'research-specialist','bibliography_readback':'verification-specialist',
         'cooling_solution':'scientific-specialist','cooling_readback':'verification-specialist'}


def fetch_noaa_metadata(station):
    from .chief_team_mission import fetch_noaa_metadata as original
    return original(station)


def parse_contract_mission(event):
    issue=event.get('issue') or {}
    lines=(issue.get('body') or '').splitlines()
    if issue.get('title') != '[Plenum Chief] public mission' or len(lines)!=2 or lines[0]!=MAGIC:
        raise PermissionError('Original founder contract mission envelope required')
    original={**event,'issue':{**issue,'title':CHIEF_TITLE,'body':CHIEF_MAGIC+'\n'+lines[1]}}
    task=parse_founder_chief(original)
    objective=task['objective']
    if re.search(r'\b(?:https?|internal|localhost)\b',objective,re.I):
        raise PermissionError('Arbitrary endpoint not permitted')
    dois=list(dict.fromkeys(x.lower().rstrip('.') for x in DOI_RE.findall(objective)))
    without_dois=DOI_RE.sub('',objective)
    stations=list(dict.fromkeys(re.findall(r'(?<![\w])([0-9]{7})(?![\w])',without_dois)))
    if stations and not re.search(r'\bNOAA\b',objective,re.I):
        raise ValueError('Station IDs require explicit NOAA scope')
    match=re.search(r'\bcooling initial ([0-9]+(?:\.[0-9]+)?) K ambient ([0-9]+(?:\.[0-9]+)?) K rate ([0-9]+(?:\.[0-9]+)?) time ([0-9]+(?:\.[0-9]+)?)\b',objective,re.I)
    cooling=dict(zip(('initial_kelvin','ambient_kelvin','rate','duration'),map(float,match.groups()))) if match else None
    if cooling and not (0 < cooling['initial_kelvin'] <= 2000 and 0 < cooling['ambient_kelvin'] <= 2000 and 0 < cooling['rate'] <= 10 and 0 < cooling['duration'] <= 10000):
        raise ValueError('Cooling parameters outside bounded physical contract')
    if not dois and not stations and not cooling or len(dois)>2 or len(stations)>3:
        raise ValueError('Require explicit bounded NOAA station or DOI identifiers')
    scope={'station_ids':stations,'dois':dois,'cooling':cooling}
    return {**task,'team':tuple(required_tools(scope)), 'scope':scope,'contract_mission':True}


def required_tools(scope):
    return (['noaa_metadata','station_validation'] if scope['station_ids'] else []) + (
        ['crossref_metadata','bibliography_readback'] if scope['dois'] else []) + (
        ['cooling_solution','cooling_readback'] if scope.get('cooling') else [])


def validate_plan(plan,scope):
    if not isinstance(plan,dict) or set(plan)!={'steps'} or not isinstance(plan['steps'],list):
        raise ValueError('Exact bounded tool plan required')
    steps=plan['steps']; expected=required_tools(scope)
    if len(steps)!=len(expected) or any(not isinstance(s,dict) for s in steps):
        raise ValueError('Omitted or repeated contract')
    names=[s.get('tool') for s in steps]
    if any(not isinstance(name,str) for name in names):raise ValueError('Tool name must be a string')
    if len(set(names))!=len(names) or set(names)!=set(expected):
        raise ValueError('Unknown, omitted or duplicate contract')
    for step in steps:
        tool=step['tool']
        dependency={'station_validation':'noaa_metadata','bibliography_readback':'crossref_metadata','cooling_readback':'cooling_solution'}.get(tool)
        if dependency:
            if step!={'tool':tool,'input_from':dependency} or names.index(dependency)>names.index(tool):
                raise ValueError('Missing or reversed actual-data dependency')
        elif step!={'tool':tool}:
            raise ValueError('Model cannot supply URLs, identifiers or executable code')
    return plan



class PlanningFailure(ValueError):
    """Fixed stage/code plus sanitized metadata; never retain provider text."""
    def __init__(self, stage, code, response=None):
        super().__init__(code)
        self.diagnostic={'stage':stage,'code':code,'response':response or {}}


def _response_info(response, parsed=None):
    raw=getattr(response,'content',None)
    info={'content_type':'string' if isinstance(raw,str) else 'list' if isinstance(raw,list) else 'other',
          'characters':len(raw) if isinstance(raw,str) else None}
    meta=getattr(response,'response_metadata',None)
    meta=meta if isinstance(meta,dict) else {}
    usage=getattr(response,'usage_metadata',None)
    usage=usage if isinstance(usage,dict) else {}
    reason=meta.get('done_reason')
    info['done_reason']=reason if reason in ('stop','length','load') else 'unknown'
    for name,value in (('input_tokens',usage.get('input_tokens',meta.get('prompt_eval_count'))),
                       ('output_tokens',usage.get('output_tokens',meta.get('eval_count')))):
        if type(value) is int and 0<=value<=10_000_000:info[name]=value
    if isinstance(parsed,dict) and isinstance(parsed.get('steps'),list):
        steps=parsed['steps'];info['step_count']=len(steps)
        info['tool_names']=[step.get('tool') if isinstance(step,dict) and isinstance(step.get('tool'),str) and step.get('tool') in TOOLS else 'UNKNOWN' for step in steps[:6]]
    return info


def _contract_error_code(exc):
    return {'Exact bounded tool plan required':'INVALID_PLAN_SHAPE',
            'Omitted or repeated contract':'CONTRACT_COUNT_MISMATCH',
            'Tool name must be a string':'INVALID_TOOL_TYPE',
            'Unknown, omitted or duplicate contract':'CONTRACT_SET_MISMATCH',
            'Missing or reversed actual-data dependency':'CONTRACT_DEPENDENCY_MISMATCH',
            'Model cannot supply URLs, identifiers or executable code':'EXTRA_CONTRACT_INPUT'}.get(str(exc),'INVALID_CONTRACT_PLAN')


def model_plan(objective,scope):
    if os.environ.get('PLENUM_EPHEMERAL_RUNNER')!='confirmed' or os.environ.get('PLENUM_CHIEF_MODEL_URL')!=MODEL_URL:
        raise PermissionError('Original isolated loopback model required')
    from langchain_ollama import ChatOllama
    choices=[{'type':'object','additionalProperties':False,'required':['tool'],
              'properties':{'tool':{'enum':['noaa_metadata','crossref_metadata','cooling_solution']}}},
             {'type':'object','additionalProperties':False,'required':['tool','input_from'],
              'properties':{'tool':{'enum':['station_validation','bibliography_readback','cooling_readback']},
                            'input_from':{'enum':['noaa_metadata','crossref_metadata','cooling_solution']}}}]
    schema={'type':'object','additionalProperties':False,'required':['steps'],
            'properties':{'steps':{'type':'array','minItems':2,'maxItems':6,'items':{'anyOf':choices}}}}
    try:
        model=ChatOllama(model=MODEL,base_url=MODEL_URL,temperature=0,reasoning=False,format=schema,num_ctx=2048,num_predict=600)
    except Exception:
        raise PlanningFailure('MODEL_CONFIGURATION','MODEL_CONFIGURATION_ERROR') from None
    try:
        response=model.invoke([('system',
            'You are the existing Plenum Chief. Compose only the public contracts needed for this explicit scope. '
            'For NOAA stations use noaa_metadata then station_validation input_from noaa_metadata. '
            'For DOI identifiers use crossref_metadata then bibliography_readback input_from crossref_metadata. '
            'For cooling parameters use cooling_solution then cooling_readback input_from cooling_solution. '
            'Combine requested domains; independent branches may be ordered either way. '
            'No absent domain, duplicate, private action, arbitrary URL, code or invented input. Return JSON only.'),
            ('human',json.dumps({'objective':objective,'authorized_identifiers':scope}))])
    except Exception:
        raise PlanningFailure('MODEL_INVOCATION','MODEL_PROVIDER_ERROR') from None
    info=_response_info(response)
    raw=getattr(response,'content',None)
    if not isinstance(raw,str) or len(raw)>4000:
        raise PlanningFailure('MODEL_RESPONSE_SHAPE','INVALID_RESPONSE_CONTENT',info)
    try:
        parsed=json.loads(raw)
    except (ValueError,TypeError):
        raise PlanningFailure('MODEL_JSON','INVALID_JSON',info) from None
    info=_response_info(response,parsed)
    try:
        return validate_plan(parsed,scope)
    except (ValueError,TypeError,KeyError) as exc:
        raise PlanningFailure('MODEL_CONTRACT_VALIDATION',_contract_error_code(exc),info) from None


def _validator(rows):
    path=Path(__file__).resolve().parents[2]/'tools/water_level_metadata.py'
    spec=importlib.util.spec_from_file_location('plenum_original_metadata_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.validate_station_metadata(rows)


def run_contract(tool,scope,prior):
    from .chief_team_mission import _station_rows
    if tool=='noaa_metadata':
        payload={station:fetch_noaa_metadata(station).decode('utf-8') for station in scope['station_ids']}
        _station_rows(payload,tuple(scope['station_ids']))
        return payload
    if tool=='station_validation':
        return _validator(_station_rows(prior['noaa_metadata'],tuple(scope['station_ids'])))
    if tool=='crossref_metadata':
        return {doi:read_crossref(doi,approved_dois=frozenset(scope['dois'])) for doi in scope['dois']}
    if tool=='bibliography_readback':
        second={doi:read_crossref(doi,approved_dois=frozenset(scope['dois'])) for doi in scope['dois']}
        if second!=prior['crossref_metadata']:
            raise ValueError('Separate Crossref provider readback disagrees')
        return {'same_provider_readback_agrees':True,'records':len(second),
                'full_paper_or_second_provider_verified':False}
    if tool=='cooling_solution':
        from scipy.integrate import solve_ivp
        p=scope['cooling']
        solution=solve_ivp(lambda t,y:(-p['rate']*(y[0]-p['ambient_kelvin']),),
                           (0,p['duration']),[p['initial_kelvin']],method='RK45',
                           rtol=1e-10,atol=1e-12,max_step=p['duration']/20)
        if not solution.success:raise ValueError('Existing SciPy solver failed')
        return {'observed_kelvin':float(solution.y[0,-1]),'library':'SciPy solve_ivp','method':'RK45','parameters':p}
    if tool=='cooling_readback':
        p=scope['cooling'];expected=p['ambient_kelvin']+(p['initial_kelvin']-p['ambient_kelvin'])*math.exp(-p['rate']*p['duration'])
        error=abs(prior['cooling_solution']['observed_kelvin']-expected)
        if not math.isfinite(error) or error>1e-6:raise ValueError('Independent analytic cooling readback disagrees')
        return {'analytic_kelvin':expected,'absolute_error_kelvin':error,'experimental_validation':False}
    raise ValueError('Unknown contract')


def verify_results(scope,results):
    from .chief_team_mission import _station_rows
    if set(results)!=set(required_tools(scope)):
        return False
    if scope['station_ids']:
        rows=_station_rows(results['noaa_metadata'],tuple(scope['station_ids']))
        if results['station_validation']!=_validator(rows):
            return False
    if scope['dois']:
        records=results['crossref_metadata']
        if (set(records)!=set(scope['dois']) or any(not isinstance(record,dict) or record.get('doi')!=doi for doi,record in records.items())
                or results['bibliography_readback']!={'same_provider_readback_agrees':True,'records':len(records),'full_paper_or_second_provider_verified':False}):
            return False
    if scope.get('cooling'):
        p=scope['cooling'];reference=p['ambient_kelvin']+(p['initial_kelvin']-p['ambient_kelvin'])*math.exp(-p['rate']*p['duration'])
        observed=results['cooling_solution'].get('observed_kelvin')
        if (not isinstance(observed,(float,int)) or isinstance(observed,bool) or not math.isfinite(observed)
                or abs(observed-reference)>1e-6 or results['cooling_solution'].get('parameters')!=p
                or results['cooling_readback'].get('analytic_kelvin')!=reference
                or results['cooling_readback'].get('absolute_error_kelvin')!=abs(observed-reference)):
            return False
    return True


def validate_inference_receipt(receipt):
    if (not isinstance(receipt,dict) or set(receipt)!={'provider','model','endpoint','structured_output'}
            or receipt['provider'] not in ('local_ollama','offline_test_planner')
            or receipt['model'] != (MODEL if receipt['provider']=='local_ollama' else None)
            or receipt['endpoint']!='loopback_only' or receipt['structured_output'] is not True):
        raise PlanningFailure('PLAN_PROVENANCE','INVALID_INFERENCE_RECEIPT')


def execute_contract_mission(event,*,output_dir,planner=None):
    task=parse_contract_mission(event);scope=task['scope'];output_dir.mkdir(parents=True,exist_ok=True)
    team=tuple(required_tools(scope))
    progress=load_checkpoint(output_dir,issue=task['issue_number'],objective=task['objective'],team=team)
    path=output_dir/f"chief-contract-plan-{task['issue_number']}.json"
    if path.exists():
        if path.is_symlink() or path.stat().st_size>8000: raise ValueError('Unsafe plan')
        receipt=json.loads(path.read_text('utf-8'))
        if set(receipt)!={'issue','objective_sha256','scope','plan','inference'} or receipt['issue']!=task['issue_number'] or receipt['objective_sha256']!=objective_digest(task['objective']) or receipt['scope']!=scope:
            raise PlanningFailure('SAVED_PLAN_BINDING','SAVED_PLAN_SCOPE_MISMATCH')
        plan=validate_plan(receipt['plan'],scope)
        validate_inference_receipt(receipt['inference'])
        called=False
    else:
        if progress: raise ValueError('Existing checkpoint cannot be replanned')
        plan=validate_plan(planner(scope) if planner else model_plan(task['objective'],scope),scope)
        receipt={'issue':task['issue_number'],'objective_sha256':objective_digest(task['objective']),'scope':scope,'plan':plan,
                 'inference':{'provider':'local_ollama' if planner is None else 'offline_test_planner','model':MODEL if planner is None else None,'endpoint':'loopback_only','structured_output':True}}
        temporary=path.with_suffix('.json.tmp')
        if temporary.is_symlink():raise ValueError('Unsafe temporary plan')
        temporary.write_text(json.dumps(receipt,sort_keys=True),'utf-8');temporary.replace(path);called=planner is None
    plan_hash=sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest()
    results={};invoked=0
    for step in plan['steps']:
        tool=step['tool'];relative=f'workers/{tool}/result.json';artifact=output_dir/relative;saved=progress.get(tool)
        if saved is not None and (not isinstance(saved,dict) or saved.get('plan_sha256')!=plan_hash):raise ValueError('Changed checkpoint plan')
        if saved and saved.get('verified'):
            if saved.get('artifact_path')!=relative or saved.get('output_artifact')!=relative or verified_previous_result(output_dir,tool,saved) is None:
                raise ValueError('Consumed artifact changed')
            restored=json.loads(artifact.read_text('utf-8'))
            if restored.get('plan_sha256')!=plan_hash:raise ValueError('Artifact plan binding changed')
            results[tool]=restored['result'];continue
        attempt=int(saved.get('attempt',0))+1 if isinstance(saved,dict) else 1
        if attempt>2:raise ValueError('Two-attempt ceiling reached')
        progress[tool]={'attempt':attempt,'status':'RUNNING','verified':False,'plan_sha256':plan_hash}
        save_checkpoint(output_dir,issue=task['issue_number'],objective=task['objective'],team=team,results=progress)
        invoked+=1;result=run_contract(tool,scope,results)
        if artifact.is_symlink() or not artifact.resolve().is_relative_to(output_dir.resolve()):raise ValueError('Unsafe result path')
        artifact.parent.mkdir(parents=True,exist_ok=True)
        artifact.write_text(json.dumps({'plan_sha256':plan_hash,'result':result},sort_keys=True),'utf-8')
        progress[tool]={'attempt':attempt,'status':'DRAFT_READY_FOR_FOUNDER','verified':True,'worker':TOOLS[tool],
                        'artifact_path':relative,'output_artifact':relative,'sha256':artifact_digest(output_dir,relative),'plan_sha256':plan_hash}
        save_checkpoint(output_dir,issue=task['issue_number'],objective=task['objective'],team=team,results=progress)
        results[tool]=result
    valid=verify_results(scope,results)
    return {'schema':'plenum-chief-founder-team-v2','mode':'multi','issue_number':task['issue_number'],
            'status':'VERIFIED_BOUNDED_CONTRACT_MISSION' if valid else 'BLOCKED_CONTRACT_INTEGRITY',
            'dispatcher':'original_chief_local_model_public_contract_composition',
            'model_called':called,'chief_model_delegated':called,'inference_provenance':receipt['inference'],
            'expected_team':list(team),'bounded_contracts_verified':valid,
            'founder_objective_verified':False,'objective_review_required':True,'independent_verified':valid,
            'worker_artifacts_technically_verified':valid,'tool_outputs_verified':valid,
            'executed_workers':len(results),'new_worker_invocations':invoked,'reused_prior_verified_workers':len(results)-invoked,
            'specialists':[TOOLS[x['tool']] for x in plan['steps']], 'contract_results':results,
            'worker_results':[{'kind':x['tool'],'worker':TOOLS[x['tool']],'status':'DRAFT_READY_FOR_FOUNDER','output_artifact':f"workers/{x['tool']}/result.json",'verified_scope':'explicit public identifier contract only'} for x in plan['steps']],
            'plan_artifact':path.name,'plan_sha256':plan_hash,'paid_api_used':False,'external_account_changes':False,
            'bounded_founder_goal_evidence':{'status':'VERIFIED_PUBLIC_CONTRACTS_NOT_FREEFORM_OBJECTIVE' if valid else 'NOT_VERIFIED'},
            'founder_review_required':True,'new_general_agent_capability_claimed':False,
            'limitations':['Freeform objective requires independent review','Crossref uses same-provider metadata readback, not full paper review','NOAA datum and instrument accuracy not checked']}

