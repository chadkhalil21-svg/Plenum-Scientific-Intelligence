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

async def _index_and_score(questions=QUERIES, ndim=256):
    from paperqa import Docs, SparseEmbeddingModel, Settings

    settings=Settings(parsing={"use_doc_details":False,"defer_embedding":False})
    embedding=SparseEmbeddingModel(ndim=ndim)
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
    for query,expected in questions:
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


# REAL approved public-source intake for existing scientific Research division.
# Reuse pypdf's established PDF text extraction and our already pinned PaperQA2
# sparse retrieval. No browser, model inference, custom parser or private input.
GREENFEED_PDF_URL = (
    "https://www.ars.usda.gov/ARSUserFiles/np212/Greenhouse/"
    "GHG%20Research%20Network%20-%20enteric%20GreenFeed%20protocol%20final.pdf"
)
GREENFEED_TITLE = "Recommended Protocol for Using the GreenFeed System"
MAX_PDF_BYTES = 8_000_000
SOURCE_TERMS = ("calibration", "recovery", "airflow", "visits")


def _acquire_approved_greenfeed(*, opener=None):
    """One first-party HTTPS PDF, strictly bounded; no arbitrary URL or redirects."""
    from io import BytesIO
    from urllib.request import Request, build_opener
    from .chief_of_staff_pilot import NoRedirects
    from pypdf import PdfReader

    client = opener or build_opener(NoRedirects)
    request = Request(
        GREENFEED_PDF_URL, method="GET",
        headers={"Accept": "application/pdf", "User-Agent": "PlenumPublicScientificResearch/1"},
    )
    with client.open(request, timeout=25) as reply:
        if reply.status != 200 or reply.geturl() != GREENFEED_PDF_URL:
            raise ValueError("Original USDA document did not return exact approved URL")
        if "application/pdf" not in reply.headers.get("Content-Type", "").lower():
            raise ValueError("USDA source did not return a PDF")
        raw = reply.read(MAX_PDF_BYTES + 1)
    if len(raw) > MAX_PDF_BYTES or len(raw) < 1000 or not raw.startswith(b"%PDF-"):
        raise ValueError("Unsafe or malformed public source document")
    reader = PdfReader(BytesIO(raw), strict=False)
    if reader.is_encrypted or not 20 <= len(reader.pages) <= 50:
        raise ValueError("Unexpected public USDA PDF page count or encrypted input")
    pages = [(" ".join((page.extract_text() or "").split())) for page in reader.pages]
    if len(pages[0]) < 100 or GREENFEED_TITLE.casefold() not in pages[0].casefold():
        raise ValueError("USDA document identity cannot be verified from extracted page 1")
    if "25 November 2024" not in pages[0]:
        raise ValueError("Unexpected source revision or first-page date")
    if sum(map(len, pages)) < 12000 or sum(map(len, pages)) > 250000:
        raise ValueError("Unusable public-source PDF text quantity")
    return raw, pages


async def _index_real_greenfeed(pages, tempdir):
    """The EXISTING upstream PaperQA2 engine, no paid LLM or embedding service."""
    from paperqa import Docs, SparseEmbeddingModel, Settings

    path = Path(tempdir) / "approved-usda-greenfeed-2024.md"
    path.write_text(
        "\n\n".join(
            f"## USDA ARS protocol PDF page {n + 1}\n\n{page}"
            for n, page in enumerate(pages)
        ) + "\n", encoding="utf-8",
    )
    settings = Settings(parsing={"use_doc_details": False, "defer_embedding": False})
    model = SparseEmbeddingModel(ndim=256)
    docs = Docs()
    added = await docs.aadd(
        path, citation="USDA ARS (2024), GreenFeed cattle GHG measurement protocol",
        docname="approved_usda_greenfeed_2024", settings=settings,
        embedding_model=model,
    )
    if not added:
        raise ValueError("Existing PaperQA2 did not index real USDA document")
    matches = await docs.retrieve_texts(
        "GreenFeed methane cattle measurement calibration recovery airflow visits",
        1, settings=settings, embedding_model=model,
    )
    return bool(matches and matches[0].doc.docname == "approved_usda_greenfeed_2024")


def run_greenfeed_public():
    """Actual independent evidence, not a repeat of old local sample QA."""
    import asyncio
    import tempfile
    from unittest.mock import patch

    if importlib.metadata.version("paper-qa") != VERSION:
        raise RuntimeError("Unreviewed original PaperQA2 version")
    raw, pages = _acquire_approved_greenfeed()
    evidence = []
    for term in SOURCE_TERMS:
        found = next(
            ((n + 1, page) for n, page in enumerate(pages)
             if term in page.casefold()), None
        )
        if not found:
            raise ValueError("A required technical section is missing in USDA source")
        num, page = found
        at = page.casefold().index(term)
        evidence.append({
            "topic": term, "pdf_page": num,
            "source_text_excerpt": page[max(0, at - 65):at + 220],
        })
    with tempfile.TemporaryDirectory(prefix="plenum-public-paperqa-") as tmp:
        # The public PDF was acquired exactly once; no network during PaperQA2.
        with patch("socket.socket.connect", _blocked_connect):
            retrieved = asyncio.run(_index_real_greenfeed(pages, tmp))
    if not retrieved:
        raise ValueError("PaperQA2 did not return the actual approved document")
    return {
        "schema": "plenum-greenfeed-real-public-source-v1",
        "status": "REAL_PUBLIC_DOCUMENT_INDEXED_AND_SOURCE_READ",
        "source_url": GREENFEED_PDF_URL,
        "source_sha256": sha256(raw).hexdigest(),
        "source_provider": "United States Department of Agriculture Agricultural Research Service",
        "source_date": "2024-11-25",
        "source_pages_extracted": len(pages),
        "source_text_characters": sum(map(len, pages)),
        "source_linked_excerpts": evidence,
        "upstream_pdf_parser": "pypdf",
        "upstream_research_engine": "paper-qa",
        "research_engine_version": VERSION,
        "paperqa_actual_index_and_retrieval": True,
        "source_identity_checked_from_pdf": True,
        "source_sections_observed": len(evidence),
        "no_new_model": True,
        "model_calls": 0,
        "paid_api_calls": 0,
        "private_accounts_accessed": False,
        "generated_science_conclusion": False,
        "terra_efficacy_verified": False,
        "general_autonomous_agent_verified": False,
    }


def main():
    cli=argparse.ArgumentParser(description="No-LLM upstream PaperQA2 retrieval evaluation")
    cli.add_argument("--execute",action="store_true")
    cli.add_argument("--usda-greenfeed", action="store_true",
                     help="Retrieve and index one exact authorized PUBLIC USDA PDF, using existing PaperQA2")
    cli.add_argument("--out",default="reports/paperqa-public-retrieval.json")
    args=cli.parse_args()
    out=Path(args.out)
    if (out.is_absolute() or ".." in out.parts or out.suffix!=".json"
        or not out.parts or out.parts[0]!="reports" or len(out.parts)>4):
        raise ValueError("Only bounded JSON under reports/ accepted")
    result=(run_greenfeed_public() if args.usda_greenfeed else run()) if args.execute else (
        {"status": "APPROVED_PUBLIC_SOURCE_PLAN_ONLY", "source_url": GREENFEED_PDF_URL,
         "network_used": False, "paid_api_calls": 0, "model_calls": 0}
        if args.usda_greenfeed else plan()
    )
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PaperQA2 source retrieval:",result.get("correct","dry run"),
          "/",result.get("attempted","not executed"))

if __name__=="__main__":
    main()
