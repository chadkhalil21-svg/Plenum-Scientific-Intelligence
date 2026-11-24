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
         'cooling_solution':'scientific-specialist','cooling_readback':'verification-specialist',
         'evidence_report':'chief-evidence-assembly',
         'business_readback':'commercial-operations-specialist',
         'business_review':'verification-specialist',
         'paper_discovery':'research-specialist','paper_readback':'verification-specialist'}


DEPENDENCIES = {'station_validation':'noaa_metadata',
                'bibliography_readback':'crossref_metadata',
                'cooling_readback':'cooling_solution', 'business_review':'business_readback', 'paper_readback':'paper_discovery'}
ACCEPTANCE = {'noaa_metadata':'exact_station_identity_and_coordinates',
              'station_validation':'exact_input_structural_validation',
              'crossref_metadata':'exact_doi_and_required_metadata',
              'bibliography_readback':'same_provider_metadata_agreement',
              'cooling_solution':'finite_temperature_within_analytic_tolerance',
              'cooling_readback':'independent_analytic_temperature_agreement',
              'evidence_report':'complete_source_bound_evidence_report',
              'business_readback':'all_original_public_targets_checked_with_bounded_attempts',
              'business_review':'exact_business_status_readback_without_readiness_claim',
              'paper_discovery':'bounded_topic_matched_doi_discovery',
              'paper_readback':'artifact_selected_doi_identity_title_publisher_year'}


def contract_dependencies(tool, scope):
    if tool == 'evidence_report':
        return [name for name in required_tools(scope) if name != tool]
    return [DEPENDENCIES[tool]] if tool in DEPENDENCIES else []


def contract_goal_graph(plan, scope):
    """Derive the trusted goal criteria from the original authorized contracts."""
    from .chief_team_mission import validate_specialist_graph
    checked = validate_plan(plan, scope)
    approved = {tool: {'specialist': TOOLS[tool],
                       'depends_on': contract_dependencies(tool, scope),
                       'acceptance': ACCEPTANCE[tool]}
                for tool in required_tools(scope)}
    proposed = [{'id': step['tool'], 'specialist': TOOLS[step['tool']],
                 'depends_on': contract_dependencies(step['tool'], scope),
                 'acceptance': ACCEPTANCE[step['tool']]}
                for step in checked['steps']]
    return validate_specialist_graph(proposed, approved)


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
    business_scope=objective.startswith('Evidence report ') and 'American Rider public health' in objective[len('Evidence report '):].split(' and ')
    from .world_horizon import paper_survey_subject
    paper_clauses=[clause for clause in objective[len('Evidence report '):].split(' and ')
                   if paper_survey_subject(clause)] if objective.startswith('Evidence report ') else []
    if len(paper_clauses)>1:
        raise ValueError('Only one explicit topic survey per report')
    if (not dois and not stations and not cooling and not business_scope and not paper_clauses) or len(dois)>2 or len(stations)>3:
        raise ValueError('Require explicit bounded NOAA station or DOI identifiers')
    scope={'station_ids':stations,'dois':dois,'cooling':cooling}
    if business_scope:
        scope['business']=True
    if paper_clauses:
        scope['paper_survey']=paper_clauses[0]
    # The complete deliverable is independently gradeable only under this
    # exact, fully consumed report grammar. Other goals retain legacy scope.
    if objective.startswith('Evidence report '):
        clauses=objective[len('Evidence report '):].split(' and ')
        kinds=[]
        for clause in clauses:
            if re.fullmatch(r'NOAA [0-9]{7}(?: [0-9]{7}){0,2}',clause):
                kinds.append('station_ids')
            elif re.fullmatch(r'DOI '+DOI_RE.pattern+r'(?: '+DOI_RE.pattern+r')?',clause):
                kinds.append('dois')
            elif re.fullmatch(r'cooling initial [0-9]+(?:\.[0-9]+)? K ambient [0-9]+(?:\.[0-9]+)? K rate [0-9]+(?:\.[0-9]+)? time [0-9]+(?:\.[0-9]+)?',clause):
                kinds.append('cooling')
            elif clause=='American Rider public health':
                kinds.append('business')
            elif paper_survey_subject(clause):
                kinds.append('paper_survey')
            else:
                raise ValueError('Unsupported evidence report clause')
        if len(kinds)!=len(set(kinds)) or set(kinds)!={k for k,v in scope.items() if v}:
            raise ValueError('Repeated or unparsed evidence report clause')
        scope['evidence_report']=True
    return {**task,'team':tuple(required_tools(scope)), 'scope':scope,'contract_mission':True}


def required_tools(scope):
    return (['noaa_metadata','station_validation'] if scope['station_ids'] else []) + (
        ['crossref_metadata','bibliography_readback'] if scope['dois'] else []) + (
        ['cooling_solution','cooling_readback'] if scope.get('cooling') else []) + (
        ['business_readback','business_review'] if scope.get('business') else []) + (
        ['paper_discovery','paper_readback'] if scope.get('paper_survey') else []) + (
        ['evidence_report'] if scope.get('evidence_report') else [])


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
        dependencies=contract_dependencies(tool,scope)
        if dependencies:
            input_from=dependencies if tool=='evidence_report' else dependencies[0]
            if step!={'tool':tool,'input_from':input_from} or any(names.index(dep)>names.index(tool) for dep in dependencies):
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
    # Use the ORIGINAL validated scope to prevent an on-run model from
    # proposing unrelated specialist tools (e.g. cooling with only NOAA+DOI).
    # Strict validate_plan below still rejects duplicates and bad dependencies.
    expected=required_tools(scope)
    allowed=set(expected)
    if scope.get('evidence_report'):
        raise PlanningFailure('MODEL_CONFIGURATION','EXPLICIT_REPORT_REQUIRES_DETERMINISTIC_GRAPH')
    choices=[]
    for source,check in (('noaa_metadata','station_validation'),
                         ('crossref_metadata','bibliography_readback'),
                         ('cooling_solution','cooling_readback')):
        if source in allowed:
            choices.extend([
                {'type':'object','additionalProperties':False,'required':['tool'],
                 'properties':{'tool':{'enum':[source]}}},
                {'type':'object','additionalProperties':False,'required':['tool','input_from'],
                 'properties':{'tool':{'enum':[check]},'input_from':{'enum':[source]}}}
            ])
    schema={'type':'object','additionalProperties':False,'required':['steps'],
            'properties':{'steps':{'type':'array','minItems':len(expected),
                                   'maxItems':len(expected),'items':{'anyOf':choices}}}}
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
        if not solution.success:raise RuntimeError('Existing SciPy solver failed')
        return {'observed_kelvin':float(solution.y[0,-1]),'library':'SciPy solve_ivp','method':'RK45','parameters':p}
    if tool=='cooling_readback':
        p=scope['cooling'];expected=p['ambient_kelvin']+(p['initial_kelvin']-p['ambient_kelvin'])*math.exp(-p['rate']*p['duration'])
        error=abs(prior['cooling_solution']['observed_kelvin']-expected)
        if not math.isfinite(error) or error>1e-6:raise ValueError('Independent analytic cooling readback disagrees')
        return {'analytic_kelvin':expected,'absolute_error_kelvin':error,'experimental_validation':False}
    if tool=='business_readback':
        from .business_public_watch import run
        return run()
    if tool=='business_review':
        return review_business_status(prior['business_readback'])
    if tool=='paper_discovery':
        from .world_horizon import scan_horizon
        return scan_horizon(scope['paper_survey'],category='journals',online=True)
    if tool=='paper_readback':
        selected=selected_paper_ids(scope,prior['paper_discovery'])
        return {doi:read_crossref(doi,approved_dois=frozenset(selected)) for doi in selected}
    if tool=='evidence_report':
        return build_evidence_report(scope, prior)
    raise ValueError('Unknown contract')


def review_business_status(report):
    """Validate the real original monitor's receipt, not a new network request.

    An unavailable endpoint is a valid finding, never a green availability
    claim. All three original endpoint observations must be accounted for.
    """
    from .business_public_watch import TARGETS
    from datetime import datetime
    if (not isinstance(report,dict)
            or report.get('schema')!='plenum-public-business-readback-v1'
            or report.get('scope')!='public_https_read_only'
            or report.get('total')!=len(TARGETS)
            or any(report.get(k) is not False for k in
                   ('asserts_commercial_readiness','asserts_transaction_success','requires_production_credentials'))):
        raise ValueError('Invalid public business monitor receipt')
    stamp=datetime.fromisoformat(report['checked_at_utc'])
    if stamp.tzinfo is None:
        raise ValueError('Business observation time must be timezone aware')
    rows=report.get('reports')
    if (not isinstance(rows,list) or len(rows)!=len(TARGETS)
            or any(not isinstance(row,dict) for row in rows)
            or [row.get('service') for row in rows]!=[target.name for target in TARGETS]):
        raise ValueError('Business monitor did not account for every original target')
    good=0
    for row in rows:
        attempts=row.get('attempts')
        if type(attempts) is not int or not 1<=attempts<=6 or row.get('external_actions_executed') is not False:
            raise ValueError('Unsafe public business observation')
        if row.get('status')=='PUBLIC_HTTP_VERIFIED':
            if row.get('independent_gets')!=2 or attempts<2 or row.get('http')!=200:
                raise ValueError('Missing double readback evidence')
            good+=1
        elif row.get('status')=='UNVERIFIED':
            if row.get('phase') not in ('initial','readback') or not isinstance(row.get('reason'),str):
                raise ValueError('Missing failed observation evidence')
        else:
            raise ValueError('Unrecognized business observation state')
    if type(report.get('verified')) is not int or report['verified']!=good:
        raise ValueError('Business monitor counts disagree')
    return {'all_targets_accounted_for':True,'verified_endpoints':good,
            'unverified_endpoints':len(TARGETS)-good,'all_endpoints_verified':good==len(TARGETS),
            'commercial_readiness_verified':False,'transactions_verified':False}


def selected_paper_ids(scope, report):
    """Only actual bounded, topic-matched deposited DOI records authorize readback."""
    from .world_horizon import paper_survey_subject,paper_title_matches
    subject=paper_survey_subject(scope['paper_survey'])
    if (not subject or not isinstance(report,dict)
            or report.get('schema')!='plenum-public-horizon-snapshot-v1'
            or report.get('topic')!=scope['paper_survey'] or report.get('category')!='journals'
            or report.get('independent_breakthrough_verified') is not False):
        raise ValueError('Invalid topic discovery artifact')
    rows=report.get('records')
    if not isinstance(rows,list) or not 1<=len(rows)<=4:
        raise ValueError('Missing bounded paper discovery')
    selected=[]
    for row in rows:
        if (not isinstance(row,dict) or row.get('source')!='crossref_journals'
                or row.get('category')!='journals'
                or row.get('independent_fact_check_complete') is not False
                or not paper_title_matches(subject,row.get('title'))
                or not isinstance(row.get('url'),str)
                or not row['url'].startswith('https://doi.org/')):
            raise ValueError('Untrusted or irrelevant discovered paper')
        doi=row['url'][len('https://doi.org/'):].lower()
        if not DOI_RE.fullmatch(doi) or doi in selected:
            raise ValueError('Invalid or duplicate discovered DOI')
        selected.append(doi)
    return selected[:2]


def verify_paper_readback(scope, discovery, result):
    from .world_horizon import paper_survey_subject,paper_title_matches
    try:
        selected=selected_paper_ids(scope,discovery)
        rows={r['url'][len('https://doi.org/'):].lower():r for r in discovery['records']}
        subject=paper_survey_subject(scope['paper_survey'])
        return (isinstance(result,dict) and set(result)==set(selected)
                and all(isinstance(record,dict) and record.get('doi')==doi
                        and record.get('title')==rows[doi]['title']
                        and paper_title_matches(subject,record['title'])
                        and type(record.get('year')) is int and 1900<=record['year']<=2100
                        and isinstance(record.get('publisher'),str) and bool(record['publisher'].strip())
                        for doi,record in result.items()))
    except (ValueError,TypeError,KeyError,AttributeError):
        return False


def build_evidence_report(scope, inputs):
    """Engineering handoff: a compact, useful report from actual producer bytes."""
    from .chief_team_mission import _station_rows
    report={'schema':'plenum-source-bound-evidence-report-v1','sections':{}}
    if scope['station_ids']:
        rows=_station_rows(inputs['noaa_metadata'],tuple(scope['station_ids']))
        report['sections']['stations']={
            'records':[{key:row.get(key) for key in ('id','name','lat','lng')} for row in rows],
            'validation':inputs['station_validation'],
            'source':'NOAA CO-OPS station metadata',
            'limitation':'Structural metadata only; no datum or instrument accuracy verification'}
    if scope['dois']:
        report['sections']['bibliography']={
            'records':[inputs['crossref_metadata'][doi] for doi in scope['dois']],
            'readback':inputs['bibliography_readback'],
            'limitation':'Crossref deposited metadata and same-provider readback; not paper-content verification'}
    if scope.get('cooling'):
        report['sections']['cooling']={
            'solution':inputs['cooling_solution'],'readback':inputs['cooling_readback'],
            'limitation':'Analytic and numerical model only; no experimental validation'}
    if scope.get('business'):
        report['sections']['business']={
            'observation':inputs['business_readback'],'review':inputs['business_review'],
            'limitation':'Public HTTP availability only; no transaction or commercial readiness verification'}
    if scope.get('paper_survey'):
        report['sections']['papers']={'discovery':inputs['paper_discovery'],
            'readback':inputs['paper_readback'],
            'limitation':'Topic-matched discovery and separate Crossref metadata readback only; no full paper or scientific claim verification'}
    return report


def verify_evidence_report(scope, inputs, report):
    """Independently check completeness and each section against source outputs."""
    if not isinstance(report,dict) or set(report)!={'schema','sections'} or report['schema']!='plenum-source-bound-evidence-report-v1':
        return False
    sections=report['sections']
    expected=set()
    if scope['station_ids']: expected.add('stations')
    if scope['dois']: expected.add('bibliography')
    if scope.get('cooling'): expected.add('cooling')
    if scope.get('business'): expected.add('business')
    if scope.get('paper_survey'): expected.add('papers')
    if not isinstance(sections,dict) or set(sections)!=expected:
        return False
    try:
        if 'stations' in sections:
            from .chief_team_mission import _station_rows
            section=sections['stations']
            if set(section)!={'records','validation','source','limitation'} or section['source']!='NOAA CO-OPS station metadata' or section['limitation']!='Structural metadata only; no datum or instrument accuracy verification':
                return False
            rows=_station_rows(inputs['noaa_metadata'],tuple(scope['station_ids']))
            if len(section['records'])!=len(rows) or section['validation']!=_validator(rows):
                return False
            for observed, original in zip(section['records'],rows):
                if set(observed)!={'id','name','lat','lng'} or any(observed[k]!=original.get(k) for k in observed):
                    return False
        if 'bibliography' in sections:
            section=sections['bibliography']
            if set(section)!={'records','readback','limitation'} or section['limitation']!='Crossref deposited metadata and same-provider readback; not paper-content verification':
                return False
            if section['records']!=[inputs['crossref_metadata'][doi] for doi in scope['dois']] or section['readback']!=inputs['bibliography_readback']:
                return False
        if 'cooling' in sections:
            section=sections['cooling']
            if set(section)!={'solution','readback','limitation'} or section['limitation']!='Analytic and numerical model only; no experimental validation':
                return False
            if section['solution']!=inputs['cooling_solution'] or section['readback']!=inputs['cooling_readback']:
                return False
        if 'business' in sections:
            section=sections['business']
            if set(section)!={'observation','review','limitation'} or section['limitation']!='Public HTTP availability only; no transaction or commercial readiness verification':
                return False
            if section['observation']!=inputs['business_readback'] or section['review']!=review_business_status(inputs['business_readback']) or section['review']!=inputs['business_review']:
                return False
        if 'papers' in sections:
            section=sections['papers']
            if (set(section)!={'discovery','readback','limitation'}
                    or section['limitation']!='Topic-matched discovery and separate Crossref metadata readback only; no full paper or scientific claim verification'
                    or section['discovery']!=inputs['paper_discovery']
                    or section['readback']!=inputs['paper_readback']
                    or not verify_paper_readback(scope,section['discovery'],section['readback'])):
                return False
        return True
    except (ValueError,TypeError,KeyError,AttributeError):
        return False


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
    if scope.get('business') and results['business_review']!=review_business_status(results['business_readback']):
        return False
    if scope.get('paper_survey') and not verify_paper_readback(scope,results['paper_discovery'],results['paper_readback']):
        return False
    if scope.get('evidence_report') and not verify_evidence_report(scope,results,results['evidence_report']):
        return False
    return True


def validate_inference_receipt(receipt):
    expected={'local_ollama':(MODEL,'loopback_only',True),
              'offline_test_planner':(None,'loopback_only',True),
              'deterministic_contract_router':(None,'not_used',False)}
    if (not isinstance(receipt,dict) or set(receipt)!={'provider','model','endpoint','structured_output'}
            or not isinstance(receipt['provider'],str) or receipt['provider'] not in expected
            or (receipt['model'],receipt['endpoint'],receipt['structured_output']) != expected[receipt['provider']]
            or type(receipt['structured_output']) is not bool):
        raise PlanningFailure('PLAN_PROVENANCE','INVALID_INFERENCE_RECEIPT')


def deterministic_scope_plan(scope):
    """Use original source/check tools for every explicit, bounded public scope.

    The original local planner invented cooling tools for NOAA+DOI issue #679
    (run 43642394223), resulting in zero work. Tool dependencies are already
    fixed and validated: a model cannot improve this exact scope decision.
    This ONLY handles founder-whitelisted identifiers and source/readback pairs.
    """
    steps=[]
    for tool in required_tools(scope):
        dependencies=contract_dependencies(tool,scope)
        step={'tool':tool}
        if dependencies:
            step['input_from']=dependencies if tool=='evidence_report' else dependencies[0]
        steps.append(step)
    return validate_plan({'steps':steps},scope)


def deterministic_pair_plan(scope):
    """Legacy public scope helper preserved for existing call sites."""
    return deterministic_scope_plan(scope)


CONTRACT_ARTIFACT_SCHEMA = 'plenum-chief-contract-result-v2'


def read_contract_artifact(root, tool, entry, plan_hash):
    relative = f'workers/{tool}/result.json'
    if (entry.get('artifact_path') != relative or entry.get('output_artifact') != relative
            or verified_previous_result(root, tool, entry) is None):
        raise ValueError('Consumed artifact changed')
    record = json.loads((root / relative).read_text('utf-8'))
    if (not isinstance(record, dict) or record.get('plan_sha256') != plan_hash
            or 'result' not in record
            or ('schema' in record and record['schema'] != CONTRACT_ARTIFACT_SCHEMA)):
        raise ValueError('Artifact plan binding changed')
    return record


def cooling_matrix_solution(parameters):
    """Propagate the temperature deviation with a matrix exponential on recovery."""
    from scipy.linalg import expm
    exponent = -parameters['rate'] * parameters['duration']
    factor = float(expm([[exponent]])[0, 0])
    ambient = parameters['ambient_kelvin']
    temperature = ambient + (parameters['initial_kelvin'] - ambient) * factor
    return {'observed_kelvin': temperature, 'library': 'SciPy linalg.expm',
            'method': 'expm', 'parameters': parameters}


class CoolingQualityFailure(RuntimeError):
    """A producer returned an invalid result, not merely a transport failure."""


def check_cooling_producer(parameters, result):
    """Check correctness before reserving a verified producer receipt."""
    reference = parameters['ambient_kelvin'] + (
        parameters['initial_kelvin'] - parameters['ambient_kelvin']
    ) * math.exp(-parameters['rate'] * parameters['duration'])
    observed = result.get('observed_kelvin') if isinstance(result, dict) else None
    if (not isinstance(observed, (float, int)) or isinstance(observed, bool)
            or not math.isfinite(observed) or abs(observed - reference) > 1e-6
            or result.get('parameters') != parameters):
        raise CoolingQualityFailure('Cooling producer failed analytic acceptance')


def check_contract_result(tool, scope, inputs, result):
    """Apply each node's trusted quality criterion before accepting its artifact."""
    from .chief_team_mission import _station_rows
    if tool == 'cooling_solution':
        check_cooling_producer(scope['cooling'], result)
        return
    if tool == 'noaa_metadata':
        _station_rows(result, tuple(scope['station_ids']))
        return
    if tool == 'station_validation':
        if result == _validator(_station_rows(inputs['noaa_metadata'], tuple(scope['station_ids']))):
            return
    elif tool == 'crossref_metadata':
        if (isinstance(result, dict) and set(result) == set(scope['dois'])
                and all(isinstance(record, dict) and record.get('doi') == doi
                        and isinstance(record.get('title'), str) and bool(record['title'].strip())
                        and type(record.get('year')) is int
                        and isinstance(record.get('publisher'), str) and bool(record['publisher'].strip())
                        for doi, record in result.items())):
            return
    elif tool == 'bibliography_readback':
        if result == {'same_provider_readback_agrees':True,
                      'records':len(inputs['crossref_metadata']),
                      'full_paper_or_second_provider_verified':False}:
            return
    elif tool == 'cooling_readback':
        p = scope['cooling']
        reference = p['ambient_kelvin'] + (p['initial_kelvin'] - p['ambient_kelvin']) * math.exp(-p['rate'] * p['duration'])
        error = abs(inputs['cooling_solution']['observed_kelvin'] - reference)
        if (math.isfinite(error) and error <= 1e-6
                and result == {'analytic_kelvin':reference, 'absolute_error_kelvin':error,
                               'experimental_validation':False}):
            return
    elif tool == 'business_readback':
        review_business_status(result)
        return
    elif tool == 'business_review':
        if result==review_business_status(inputs['business_readback']):
            return
    elif tool == 'paper_discovery':
        selected_paper_ids(scope,result)
        return
    elif tool == 'paper_readback':
        if verify_paper_readback(scope,inputs['paper_discovery'],result):
            return
    elif tool == 'evidence_report':
        if verify_evidence_report(scope,inputs,result):
            return
    raise ValueError('Specialist result failed its trusted acceptance criterion')


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
        # For ALL exact founder-authorized NOAA / DOI / cooling combinations,
        # the original pair dependencies are already fully specified. No
        # Qwen/Ollama invocation or free runner model startup is necessary.
        # An explicitly injected offline planner remains for regression
        # compatibility, but cannot bypass the original validate_plan gate.
        if planner is None:
            plan=deterministic_scope_plan(scope)
            inference={'provider':'deterministic_contract_router','model':None,'endpoint':'not_used','structured_output':False}
        else:
            plan=validate_plan(planner(scope),scope)
            inference={'provider':'offline_test_planner','model':None,'endpoint':'loopback_only','structured_output':True}
        receipt={'issue':task['issue_number'],'objective_sha256':objective_digest(task['objective']),'scope':scope,'plan':plan,'inference':inference}
        temporary=path.with_suffix('.json.tmp')
        if temporary.is_symlink():raise ValueError('Unsafe temporary plan')
        temporary.write_text(json.dumps(receipt,sort_keys=True),'utf-8');temporary.replace(path);called=False
    plan_hash=sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest()
    graph = contract_goal_graph(plan, scope)
    results = {}
    invoked = 0
    reused = 0
    for node in graph:
        tool = node['id']
        dependencies = node['depends_on']
        relative = f'workers/{tool}/result.json'
        artifact = output_dir / relative
        saved = progress.get(tool)
        if saved is not None and (not isinstance(saved, dict) or saved.get('plan_sha256') != plan_hash):
            raise ValueError('Changed checkpoint plan')

        # Re-open the producer's durable bytes at the consumer boundary.
        inputs = {}
        input_digests = {}
        sources = {}
        for dependency in dependencies:
            source = read_contract_artifact(output_dir, dependency, progress[dependency], plan_hash)
            sources[dependency] = source
            inputs[dependency] = source['result']
            input_digests[dependency] = progress[dependency]['sha256']

        if saved and saved.get('verified'):
            restored = read_contract_artifact(output_dir, tool, saved, plan_hash)
            if tool == 'evidence_report':
                if restored.get('input_digests') != input_digests:
                    raise ValueError('Consumed dependency digests changed')
            elif dependencies and (sources[dependencies[0]].get('schema') == CONTRACT_ARTIFACT_SCHEMA
                               or 'schema' in restored or 'input_sha256' in restored):
                if restored.get('input_sha256') != input_digests[dependencies[0]]:
                    raise ValueError('Consumed dependency digest changed')
            if ('acceptance_criterion' in restored and restored['acceptance_criterion'] != node['acceptance']):
                raise ValueError('Stored acceptance criterion changed')
            check_contract_result(tool, scope, inputs, restored['result'])
            results[tool] = restored['result']
            reused += 1
            continue

        if saved and (type(saved.get('attempt')) is not int or saved.get('status') != 'RUNNING'
                      or saved.get('verified') is not False):
            raise ValueError('Invalid prior attempt')
        attempt = saved['attempt'] + 1 if saved else 1
        recovery_reason = 'interrupted_attempt' if saved else None
        if not 1 <= attempt <= 2:
            raise ValueError('Two-attempt ceiling reached')
        while True:
            progress[tool] = {'attempt': attempt, 'status': 'RUNNING', 'verified': False,
                              'plan_sha256': plan_hash}
            save_checkpoint(output_dir, issue=task['issue_number'], objective=task['objective'],
                            team=team, results=progress)
            invoked += 1
            try:
                if tool == 'cooling_solution' and attempt == 2:
                    result = cooling_matrix_solution(scope['cooling'])
                else:
                    result = run_contract(tool, scope, inputs)
                check_contract_result(tool, scope, inputs, result)
                break
            except (OSError, RuntimeError) as failure:
                if tool != 'cooling_solution' or attempt != 1:
                    raise
                recovery_reason = type(failure).__name__
                attempt += 1

        if artifact.is_symlink() or not artifact.resolve().is_relative_to(output_dir.resolve()):
            raise ValueError('Unsafe result path')
        artifact.parent.mkdir(parents=True, exist_ok=True)
        record = {'schema': CONTRACT_ARTIFACT_SCHEMA, 'plan_sha256': plan_hash,
                  'acceptance_criterion': node['acceptance'], 'result': result}
        if tool == 'cooling_solution' and attempt == 2:
            record['recovery'] = {'previous_method': 'RK45', 'method': 'expm',
                                  'reason': recovery_reason}
        if tool == 'evidence_report':
            record['input_digests'] = input_digests
        elif dependencies:
            record['input_sha256'] = input_digests[dependencies[0]]
        artifact.write_text(json.dumps(record, sort_keys=True), 'utf-8')
        digest = artifact_digest(output_dir, relative)
        if not digest:
            raise ValueError('Missing or unsafe result artifact')
        progress[tool] = {'attempt': attempt, 'status': 'DRAFT_READY_FOR_FOUNDER',
                          'verified': True, 'worker': TOOLS[tool], 'artifact_path': relative,
                          'output_artifact': relative, 'sha256': digest, 'plan_sha256': plan_hash}
        save_checkpoint(output_dir, issue=task['issue_number'], objective=task['objective'],
                        team=team, results=progress)
        results[tool] = result
    valid=verify_results(scope,results)
    report_verified=bool(valid and scope.get('evidence_report'))
    return {'schema':'plenum-chief-founder-team-v2','mode':'multi','issue_number':task['issue_number'],
            'status':'VERIFIED_BOUNDED_CONTRACT_MISSION' if valid else 'BLOCKED_CONTRACT_INTEGRITY',
            'dispatcher':(('original_chief_deterministic_public_contract_pair' if len(team)==2
                           else 'original_chief_deterministic_public_scope_contracts')
                          if receipt['inference']['provider']=='deterministic_contract_router'
                          else 'original_chief_local_model_public_contract_composition'),
            'model_called':called,'chief_model_delegated':called,'inference_provenance':receipt['inference'],
            'expected_team':list(team),'bounded_contracts_verified':valid,
            'founder_objective_verified':report_verified,'objective_review_required':not report_verified,'independent_verified':valid,
            'worker_artifacts_technically_verified':valid,'tool_outputs_verified':valid,
            'executed_workers':len(results),'new_worker_invocations':invoked,'reused_prior_verified_workers':reused,
            'specialists':[TOOLS[x['tool']] for x in plan['steps']], 'contract_results':results,
            'worker_results':[{'kind':x['tool'],'worker':TOOLS[x['tool']],'status':'DRAFT_READY_FOR_FOUNDER','output_artifact':f"workers/{x['tool']}/result.json",'verified_scope':'explicit public identifier contract only'} for x in plan['steps']],
            'plan_artifact':path.name,'plan_sha256':plan_hash,'goal_graph':graph,
            'paid_api_used':False,'external_account_changes':False,
            'bounded_founder_goal_evidence':{'status':('VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE' if report_verified else 'VERIFIED_PUBLIC_CONTRACTS_NOT_FREEFORM_OBJECTIVE' if valid else 'NOT_VERIFIED'),
                'report_artifact':'workers/evidence_report/result.json' if report_verified else None},
            'founder_review_required':not report_verified,'new_general_agent_capability_claimed':False,
            'limitations':['Freeform objective requires independent review','Crossref uses same-provider metadata readback, not full paper review','NOAA datum and instrument accuracy not checked']}
