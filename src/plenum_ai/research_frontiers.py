"""Read-only early-stage research signals from NSF and ClinicalTrials.gov.

Grant awards say what investigators were funded to attempt, not what was
discovered. Registered clinical studies say what researchers plan or have
registered, not that a treatment works. Metadata are source linked, bounded,
and never promoted to independently verified laboratory results.
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re

NSF_ENDPOINT = "https://api.nsf.gov/services/v1/awards.json"
TRIALS_ENDPOINT = "https://clinicaltrials.gov/api/v2/studies"
MAX_RESPONSE = 350_000


def _query(query):
    if not isinstance(query,str) or not 2 <= len(query.strip()) <= 140:
        raise ValueError("Public research query must be 2 to 140 characters")
    return query.strip()


def nsf_url(query):
    return NSF_ENDPOINT + "?" + urlencode({"keyword":_query(query),"rpp":3})


def trials_url(query):
    return TRIALS_ENDPOINT + "?" + urlencode({
        "query.term":_query(query), "pageSize":3,
        "sort":"LastUpdatePostDate:desc", "format":"json",
        "fields":"NCTId,BriefTitle,OverallStatus,LastUpdatePostDate",
    })


def _fetch(url, opener=urlopen):
    req = Request(url, headers={
        "User-Agent":"PlenumScientificIntelligence/1.5 research-funding-trials-metadata",
        "Accept":"application/json",
    })
    with opener(req, timeout=18) as response:
        body=response.read(MAX_RESPONSE+1)
    if len(body)>MAX_RESPONSE:
        raise ValueError("Research metadata exceeded bounded size")
    return json.loads(body)


def parse_nsf(payload):
    if not isinstance(payload,dict):
        raise ValueError("Unexpected NSF awards response")
    response=payload.get("response")
    if not isinstance(response,dict) or "award" not in response:
        raise ValueError("Missing NSF award records")
    records=response["award"]
    if not isinstance(records,list):
        raise ValueError("Invalid NSF award list")
    out=[]
    for entry in records[:3]:
        if not isinstance(entry,dict):
            continue
        ident=str(entry.get("id") or "")
        title=str(entry.get("title") or "").strip()
        if not re.fullmatch(r"\d{5,12}",ident) or len(title)<3:
            continue
        out.append({
            "source":"NSF Awards", "tier":"funded_research_project_metadata",
            "title":title[:280],
            "url":"https://www.nsf.gov/awardsearch/showAward?AWD_ID="+ident,
            "award_id":ident, "organization":str(entry.get("awardeeName") or "")[:180],
            "award_date":str(entry.get("date") or "")[:40],
            "research_conducted_or_succeeded":False,
            "experiment_results_verified":False,
        })
    return out


def parse_trials(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("studies"),list):
        raise ValueError("Unexpected ClinicalTrials.gov API v2 response")
    out=[]
    for entry in payload["studies"][:3]:
        if not isinstance(entry,dict):
            continue
        section=entry.get("protocolSection") or {}
        ident=section.get("identificationModule") or {}
        state=section.get("statusModule") or {}
        nct=str(ident.get("nctId") or "")
        title=str(ident.get("briefTitle") or "").strip()
        if not re.fullmatch(r"NCT\d{8}",nct) or len(title)<3:
            continue
        out.append({
            "source":"ClinicalTrials.gov", "tier":"registered_clinical_study_not_efficacy",
            "title":title[:280], "url":"https://clinicaltrials.gov/study/"+nct,
            "study_id":nct,
            "recruitment_status":str(state.get("overallStatus") or "unknown")[:45],
            "last_update_posted":str((state.get("lastUpdatePostDateStruct") or {}).get("date") or "")[:35],
            "study_result_verified":False,
            "clinical_approval_or_treatment_efficacy":False,
        })
    return out


def scan_frontiers(query, online=False, opener=urlopen):
    q=_query(query)
    if not online:
        return {
            "schema":"plenum-research-frontiers-v1", "query":q,
            "providers":[{"name":n,"status":"skipped_offline","records":[]} for n in ("nsf","clinicaltrials")],
            "records":[],"laboratory_breakthrough_confirmed":False,
        }
    tasks=[
        ("nsf",lambda:parse_nsf(_fetch(nsf_url(q),opener))),
        ("clinicaltrials",lambda:parse_trials(_fetch(trials_url(q),opener))),
    ]
    def perform(pair):
        name,func=pair
        try:
            records=func()
            return {"name":name,"status":"retrieved_metadata","records":records}
        except Exception as exc:
            return {"name":name,"status":"unavailable","error_type":type(exc).__name__,"records":[]}
    with ThreadPoolExecutor(max_workers=2) as pool:
        providers=list(pool.map(perform,tasks))
    return {
        "schema":"plenum-research-frontiers-v1",
        "query":q,"providers":providers,
        "records":[x for p in providers for x in p["records"]],
        "all_sources_healthy":all(p["status"]=="retrieved_metadata" for p in providers),
        "laboratory_breakthrough_confirmed":False,
        "clinical_efficacy_established":False,
        "grant_means_experiment_succeeded":False,
        "next_action":"Inspect protocols, publications, funding records and independent replication",
    }
