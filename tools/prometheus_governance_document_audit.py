"""Extract and retrieve source-linked historic hosting constraints for #432.

Fixed public repository documentation only. These are historical statements,
not present-day cloud entitlement or deployment evidence. The PDFs are local
representations of the real repository source passages, not publisher PDFs.
"""
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import textwrap

from reportlab.pdfgen.canvas import Canvas
from plenum_ai.local_document_retrieval import extract_pdf, retrieve

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ("docs/PROMETHEUS_FREE_CLOUD_STAGE1.md",
     "- Free Kaggle sessions are too ephemeral",
     "Kaggle sessions ephemeral conversational availability",
     "Free Kaggle sessions are too ephemeral"),
    ("docs/BUSINESS_WORKFORCE_OPERATIONAL_GATES.md",
     "- Free standard GitHub Actions runners",
     "ephemeral scheduled jobs permanent n8n hosting",
     "ephemeral scheduled jobs, not permanent n8n hosting"),
)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def normalized(value):
    return " ".join(value.replace("*", "").split())

def forbid_network(*args, **kwargs):
    raise RuntimeError("Network disabled during document audit")

def main():
    # No arbitrary paths, external document inputs, private records or credentials.
    socket.socket.connect = forbid_network
    socket.create_connection = forbid_network
    records, provenance = [], []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i, (relative, prefix, query, expected) in enumerate(SOURCES):
            raw = (ROOT / relative).read_bytes()
            lines = raw.decode("utf-8").splitlines()
            matches = [(n, line) for n, line in enumerate(lines, 1) if line.startswith(prefix)]
            if len(matches) != 1:
                raise ValueError("Historical source passage is missing or ambiguous")
            n, passage = matches[0]
            pdf = root / f"source-{i}.pdf"
            document = Canvas(str(pdf), invariant=1)
            document.setFont("Helvetica", 11)
            y = 740
            for line in textwrap.wrap(normalized(passage), width=85):
                document.drawString(65, y, line)
                y -= 17
            document.save()
            record = extract_pdf(root, pdf)
            assert record["source_sha256"] == sha(pdf.read_bytes())
            assert normalized(passage) in normalized(record["markdown"]), record
            records.append(record)
            provenance.append({"path": relative, "line": n,
                               "original_sha256": sha(raw),
                               "original_passage": passage,
                               "pdf_sha256": record["source_sha256"],
                               "extracted_markdown": record["markdown"]})
        evidence = []
        for (relative, prefix, query, expected), source in zip(SOURCES, provenance):
            hits = retrieve(records, query)
            accepted = [hit for hit in hits
                        if hit["source_sha256"] == source["pdf_sha256"]
                        and normalized(expected) in normalized(hit["excerpt"])]
            assert accepted, (relative, hits)
            assert all(hit["paid_inference"] is False for hit in hits)
            evidence.append({"query": query, "source_path": relative, "matched": accepted})
        report = {"schema": "plenum-real-document-audit-v1",
                  "purpose": "Recover historical hosting constraints for completion documentation",
                  "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "public_repo_development_only": True,
                  "historical_not_current_entitlement": True,
                  "pdfs_generated_from_real_source_passages": True,
                  "paid_inference": False, "provenance": provenance, "retrieval": evidence}
        (ROOT / "governance-document-audit.json").write_text(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
