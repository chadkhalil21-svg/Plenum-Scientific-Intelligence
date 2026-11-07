"""Actual PaperQA2 retrieval on pre-existing public Plenum scientific records.

No model, embeddings service, HTTP API, confidential source, or generated
scientific claim is allowed. This is retrieval evidence, NOT paper QA accuracy.
"""
import argparse
import asyncio
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
from unittest.mock import patch

SCHEMA="plenum-paperqa-public-retrieval-v1"
VERSION="2026.8.12"
ROOT=Path(__file__).resolve().parents[2]
DOCUMENTS=(
    ("battery","docs/BATTERY_MODELS.md","Plenum public battery electrochemistry"),
    ("noaa","docs/EMPIRICAL_FORECASTING.md","Plenum public coastal observations"),
)
QUERIES=(
    ("PyBaMM SPMe SPM lithium ion battery electrochemical voltage discharge","battery"),
    ("NOAA Boston Virginia Key coastal water level harmonic tide observations","noaa"),
)

def plan():
    return {"schema":SCHEMA,"package":"paper-qa","version":VERSION,
            "documents":[d[1] for d in DOCUMENTS],
            "queries":[q[0] for q in QUERIES],
            "model_calls":0,"paid_api_calls":0,"private_documents":False,
            "inference_executed":False,"retrieval_verified":False,
            "AGI_demonstrated":False,
            "limits":"Two public source retrievals only; no answer generation, semantic research understanding, or citations fact-check."}

def _blocked_connect(*args,**kwargs):
    raise RuntimeError("Network access forbidden in offline PaperQA2 pilot")

async def _index_and_score():
    from paperqa import Docs, SparseEmbeddingModel, Settings

    settings=Settings(parsing={"use_doc_details":False,"defer_embedding":False})
    embedding=SparseEmbeddingModel(ndim=256)
    docs=Docs()
    hashes={}
    for short,path,citation in DOCUMENTS:
        p=ROOT/path
        if not p.is_file() or not (50<=p.stat().st_size<=150000):
            raise ValueError("Missing or oversized reviewed public input")
        text=p.read_text(encoding="utf-8")
        if not text.strip() or "Plenum" not in text:
            raise ValueError("Unexpected public reference document")
        hashes[short]=sha256(text.encode("utf-8")).hexdigest()
        added=await docs.aadd(
            p,citation=citation,docname=short,settings=settings,
            embedding_model=embedding)
        if not added:
            raise ValueError("PaperQA2 declined to index the reviewed public document")
    results=[]
    for query,expected in QUERIES:
        matches=await docs.retrieve_texts(query,1,settings=settings,
                                         embedding_model=embedding)
        got=matches[0].doc.docname if matches else None
        results.append({"question":query,"expected":expected,"retrieved":got,
                        "correct":got==expected})
    return hashes,results

def run():
    if importlib.metadata.version("paper-qa")!=VERSION:
        raise RuntimeError("Unreviewed PaperQA2 package version")
    with patch("socket.socket.connect",_blocked_connect):
        hashes,results=asyncio.run(_index_and_score())
    return {**plan(),"inference_executed":False,"retrieval_verified":True,
            "independently_scored":True,"document_sha256":hashes,
            "retrieval_results":results,"correct":sum(r["correct"] for r in results),
            "attempted":len(results)}

def main():
    cli=argparse.ArgumentParser(description="No-LLM upstream PaperQA2 retrieval evaluation")
    cli.add_argument("--execute",action="store_true")
    cli.add_argument("--out",default="reports/paperqa-public-retrieval.json")
    args=cli.parse_args()
    out=Path(args.out)
    if (out.is_absolute() or ".." in out.parts or out.suffix!=".json"
        or not out.parts or out.parts[0]!="reports" or len(out.parts)>4):
        raise ValueError("Only bounded JSON under reports/ accepted")
    result=run() if args.execute else plan()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PaperQA2 source retrieval:",result.get("correct","dry run"),
          "/",result.get("attempted","not executed"))

if __name__=="__main__":
    main()
