"""Optional private memory backends for the ORIGINAL Plenum agents.

This module is configuration only until a user-approved private host executes it.
It never reads private chats, creates a public GitHub memory, starts a paid
provider, or replaces the existing canonical Google Drive ledger.
"""
from __future__ import annotations

import json
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

MEMORY_MCP_NPM = "@modelcontextprotocol/server-memory@2.1.1"
MEM0_PYPI = "mem0ai"
GRAPHITI_PYPI = "graphiti-core"


def installed_versions() -> dict[str, str | None]:
    """Check actual installed distributions, not their mention in pyproject."""
    found = {}
    for label, package in (("mem0", MEM0_PYPI), ("graphiti", GRAPHITI_PYPI)):
        try:
            found[label] = version(package)
        except PackageNotFoundError:
            found[label] = None
    return found


def private_storage_root() -> Path:
    """Refuse default temporary/public repository memory paths."""
    raw = os.environ.get("PLENUM_PRIVATE_MEMORY_DIR", "")
    if not raw or not Path(raw).is_absolute():
        raise RuntimeError("A private, absolute PLENUM_PRIVATE_MEMORY_DIR is required")
    path = Path(raw).resolve()
    if str(path).startswith("/tmp/") or str(path).startswith("/workspace/"):
        raise RuntimeError("Memory needs an owner-controlled persistent private directory")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise RuntimeError("Public GitHub Actions may not store founder memories")
    return path


def mcp_memory_client_entry() -> dict:
    """Owner-side MCP stdio configuration; nothing is launched automatically."""
    location = private_storage_root() / "mcp-knowledge-graph.jsonl"
    return {
        "command": "npx",
        "args": ["--yes", MEMORY_MCP_NPM],
        "env": {"MEMORY_FILE_PATH": str(location)},
    }


def create_mem0_local(*, user_id: str):
    """Use explicitly LOCAL Ollama + local persistent Qdrant; never API defaults."""
    if not user_id.strip():
        raise ValueError("Explicit user/tenant ID required")
    directory = private_storage_root() / "mem0-qdrant"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    from mem0 import Memory  # optional and deliberately lazy
    endpoint = os.environ.get("PLENUM_LOCAL_OLLAMA_URL", "http://127.0.0.1:11434")
    llm = os.environ.get("PLENUM_LOCAL_OLLAMA_MODEL", "qwen3:1.7b")
    return Memory.from_config({
        "vector_store": {"provider": "qdrant", "config": {
            "collection_name": "plenum_founder_private",
            "path": str(directory),
            "embedding_model_dims": 768,
        }},
        "llm": {"provider": "ollama", "config": {
            "model": llm, "temperature": 0, "max_tokens": 2000,
            "ollama_base_url": endpoint,
        }},
        "embedder": {"provider": "ollama", "config": {
            "model": "nomic-embed-text", "ollama_base_url": endpoint,
        }},
    })


def create_graphiti_local():
    """FalkorDB + locally hosted Ollama; caller operates both private services.

    The local model must reliably return structured JSON; small models are not
    presumed reliable. This initializer performs no ingestion or API calls.
    """
    private_storage_root()
    from graphiti_core import Graphiti  # optional and deliberately lazy
    from graphiti_core.driver.falkordb_driver import FalkorDriver
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
    uri = os.environ.get("PLENUM_LOCAL_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/") + "/v1"
    model = os.environ.get("PLENUM_LOCAL_OLLAMA_MODEL", "qwen3:1.7b")
    config = LLMConfig(api_key="ollama", model=model, small_model=model, base_url=uri)
    llm = OpenAIGenericClient(config=config)
    driver = FalkorDriver(host="127.0.0.1", port=6379, database="plenum_private")
    return Graphiti(
        graph_driver=driver, llm_client=llm,
        embedder=OpenAIEmbedder(config=OpenAIEmbedderConfig(
            api_key="ollama", embedding_model="nomic-embed-text",
            embedding_dim=768, base_url=uri,
        )),
        cross_encoder=OpenAIRerankerClient(client=llm, config=config),
    )


if __name__ == "__main__":
    print(json.dumps({
        "installed_python": installed_versions(),
        "mcp_npm_dependency": MEMORY_MCP_NPM,
        "private_disk_configured": bool(os.environ.get("PLENUM_PRIVATE_MEMORY_DIR")),
        "provider_running_verified": False,
        "chatgpt_native_memory_modified": False,
    }, indent=2))
