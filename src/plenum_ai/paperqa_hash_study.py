"""Exploratory PaperQA2 sparse retrieval: compare upstream hashing dimensions.

This test was designed AFTER inspecting one failed 256-dimension retrieval.
It is NOT a blinded model or scientific result. Keep earlier v1 report intact.
"""
import argparse
import asyncio
import importlib.metadata
import json
from pathlib import Path
import socket
from unittest.mock import patch

from .paperqa_public_retrieval import _index_and_score, _blocked_connect

VERSION="2026.8.12"
SCHEMA="plenum-paperqa-dimension-study-v1"
DIMENSIONS=(256,4096)
QUESTIONS=(
    ("PyBaMM SPM versus SPMe lithium ion discharge simulation voltage drop","battery"),
    ("Single particle electrochemistry default parameter cell modeling","battery"),
    ("How many minutes is the electrochemical discharge simulation","battery"),
    ("Battery voltage predictions versus independent discharge measurements","battery"),
    ("NOAA Boston and Virginia Key coastal tidal water level observations","noaa"),
    ("Harmonic tide forecast M2 S2 K1 O1 constituent frequencies","noaa"),
    ("June 17 observed water level MAE compared to previous day persistence","noaa"),
    ("What is the NOAA tide gauge station code for Virginia Key","noaa"),
)

def plan():
    return {
        "schema":SCHEMA,"package":"paper-qa","reviewed_version":VERSION,
        "dimensions":list(DIMENSIONS),"public_documents":2,
        "source_questions":len(QUESTIONS),
        "model_calls":0,"paid_api_calls":0,
        "private_data":False,"no_network":True,
        "results_measured":False,"AGI_demonstrated":False,
        "caveat":"Exploratory after reviewing prior retrieval failure. Existing public-source questions, not independent hidden evaluation or generated research answers.",
    }

async def _study():
    scored={}
    digests=None
    for ndim in DIMENSIONS:
        hashes, results=await _index_and_score(questions=QUESTIONS,ndim=ndim)
        if digests is not None and hashes!=digests:
            raise RuntimeError("Public document fingerprints changed between comparison arms")
        digests=hashes
        scored[str(ndim)]={
            "attempted":len(results),
            "correct":sum(bool(r["correct"]) for r in results),
            "by_question":results,
        }
    return digests,scored

def run():
    if importlib.metadata.version("paper-qa")!=VERSION:
        raise RuntimeError("Unreviewed PaperQA2 version")
    with patch.object(socket.socket,"connect",_blocked_connect):
        digests,scores=asyncio.run(_study())
    if any(row["attempted"]!=len(QUESTIONS) for row in scores.values()):
        raise RuntimeError("Not every predeclared question independently scored")
    return {
        **plan(),"results_measured":True,"source_hashes":digests,
        "results":scores,"AGI_demonstrated":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--execute",action="store_true")
    p.add_argument("--out",default="reports/paperqa-dimensions.json")
    args=p.parse_args()
    output=Path(args.out)
    if (output.is_absolute() or ".." in output.parts or output.suffix!=".json"
        or not output.parts or output.parts[0]!="reports" or len(output.parts)>4):
        raise ValueError("Only bounded JSON under reports/ permitted")
    record=run() if args.execute else plan()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print("PaperQA2 paired retrieval:",{
        key:row["correct"] for key,row in record.get("results",{}).items()
    } if args.execute else "plan only")

if __name__=="__main__":
    main()
