"""Opt-in model-free local document extraction and retrieval for Research.

Uses the original Docling native PDF pipeline and LlamaIndex simple keyword
index. No URL inputs, API keys, hosted models, private CI data or downloads at
execution. Packages must already be installed in a reviewed environment.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import os


def extract_pdf(workspace: Path, source: Path) -> dict:
    if os.getenv("GITHUB_ACTIONS") == "true":
        if os.getenv("PLENUM_PUBLIC_DOCUMENT_FIXTURE") != "confirmed":
            raise PermissionError("CI only accepts the public development fixture")
    elif os.getenv("PLENUM_OWNER_LOCAL_DOCUMENTS") != "authorized":
        raise PermissionError("Owner-authorized local document runtime required")
    root = Path(workspace)
    path = Path(source)
    if root.is_symlink() or not root.is_dir() or path.is_symlink():
        raise ValueError("Require a plain owner-selected workspace and file")
    path = path.resolve(strict=True)
    if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError("Only a local PDF in the selected workspace")
    if not 0 < path.stat().st_size <= 20 * 1024 * 1024:
        raise ValueError("PDF size outside approved bounds")
    original = path.read_bytes()
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, NativePdfFormatOption
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF],
                                  format_options={InputFormat.PDF: NativePdfFormatOption()})
    result = converter.convert(path, max_num_pages=30, max_file_size=20 * 1024 * 1024)
    markdown = result.document.export_to_markdown()
    if not markdown.strip() or len(markdown) > 500000:
        raise ValueError("Missing or oversized extracted text")
    if path.read_bytes() != original:
        raise ValueError("Source PDF changed during extraction")
    return {"source_sha256": hashlib.sha256(original).hexdigest(),
            "markdown": markdown, "paid_inference": False,
            "pipeline": "docling-native-model-free"}


def retrieve(records: list[dict], query: str) -> list[dict]:
    if not 1 <= len(records) <= 20 or not 1 <= len(query) <= 300:
        raise ValueError("Bounded retrieval required")
    from llama_index.core import Document, SimpleKeywordTableIndex
    from llama_index.core.llms import MockLLM
    from llama_index.core.embeddings import MockEmbedding
    # Explicitly prevent default hosted embedding or LLM configuration.
    from llama_index.core import Settings
    Settings.llm = MockLLM()
    Settings.embed_model = MockEmbedding(embed_dim=8)
    docs = []
    by_id = {}
    for record in records:
        if set(record) != {"source_sha256", "markdown", "paid_inference", "pipeline"}:
            raise ValueError("Only the original extraction receipt is allowed")
        digest = record["source_sha256"]
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
                or digest in by_id or record["paid_inference"] is not False
                or record["pipeline"] != "docling-native-model-free"):
            raise ValueError("Invalid or duplicate document provenance")
        body = record["markdown"]
        if not isinstance(body, str) or not 0 < len(body) <= 500000:
            raise ValueError("Invalid extracted content")
        by_id[digest] = body
        docs.append(Document(text=body, id_=digest, metadata={"source_sha256": digest}))
    index = SimpleKeywordTableIndex.from_documents(docs, llm=MockLLM())
    out = []
    for hit in index.as_retriever().retrieve(query)[:8]:
        digest = hit.node.metadata["source_sha256"]
        text = hit.node.get_content()
        if digest not in by_id or text not in by_id[digest]:
            raise ValueError("Retrieved text lacks exact source grounding")
        out.append({"source_sha256": digest, "excerpt": text, "paid_inference": False})
    return out
