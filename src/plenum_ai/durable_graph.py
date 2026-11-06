"""Persistent, read-only-on-replay LangGraph scientific investigations.

SQLite checkpoints persist on the local disk across process restarts, but
GitHub-hosted runner disks are ephemeral. Preserve/download the generated
DB artifact or use an explicitly configured persistent volume. The existing
research-memory branch holds public evidence, not automatically the DB.
"""
import os
import re
from pathlib import Path

from .parallel_research import build_graph, run_network

_THREAD_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


def validate_thread_id(value):
    if not isinstance(value, str) or not _THREAD_ID.fullmatch(value):
        raise ValueError("thread_id must be 1..80 ASCII letters, numbers, _, ., or -")
    return value


def _db_file(path):
    path = Path(path)
    if path.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
        raise ValueError("Checkpoint path must be an SQLite database file")
    if path.exists() and path.is_symlink():
        raise ValueError("Refuse to follow a symbolic-link checkpoint")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _saver():
    # Strict deserialization is recommended by the upstream checkpointer.
    os.environ["LANGGRAPH_STRICT_MSGPACK"] = "true"
    from langgraph.checkpoint.sqlite import SqliteSaver
    return SqliteSaver


def _snapshot_summary(graph, config):
    snapshot = graph.get_state(config)
    if not snapshot or not snapshot.values:
        return None
    values = snapshot.values
    return {
        "thread_id": config["configurable"]["thread_id"],
        "question": values.get("question"),
        "requested_tools": values.get("tool_keys") or [],
        "workers_recorded": len(values.get("results") or []),
        "verification": values.get("verification") or {},
        "finished": not snapshot.next,
        "replayed_without_running_tools": True,
        "claim": "checkpoint recovery only, not persistent autonomous execution",
    }


def run_persistent(question, db_path, thread_id, tool_keys=None, optimize=True,
                   offline=True):
    """A given thread can execute once; later calls recover state without rerunning."""
    validate_thread_id(thread_id)
    path = _db_file(db_path)
    Saver = _saver()
    config = {"configurable": {"thread_id": thread_id}}
    with Saver.from_conn_string(str(path)) as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        previous = _snapshot_summary(graph, config)
        if previous is not None:
            if previous["question"] != question:
                raise ValueError("Existing thread_id is bound to a different question")
            return {"status": "recovered", "checkpoint": previous,
                    "new_scientific_work_executed": False}
        result = run_network(
            question, tool_keys=tool_keys, offline=offline,
            optimize=optimize, graph=graph, invoke_config=config,
        )
        snapshot = _snapshot_summary(graph, config)
        if not snapshot or not snapshot["finished"]:
            raise RuntimeError("No completed durable LangGraph checkpoint recorded")
        if snapshot["workers_recorded"] != result["parallel_tool_count"]:
            raise RuntimeError("Durable checkpoint does not contain the expected workers")
    return {
        "status": "executed_and_checkpointed", "result": result,
        "checkpoint": snapshot, "new_scientific_work_executed": True,
        "db_file": str(path),
    }


def inspect_persistent(db_path, thread_id):
    validate_thread_id(thread_id)
    path = Path(db_path)
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("No persisted checkpoint database")
    Saver = _saver()
    with Saver.from_conn_string(str(path)) as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        snapshot = _snapshot_summary(graph, {"configurable":{"thread_id":thread_id}})
        if snapshot is None:
            raise KeyError("No recorded checkpoint for this thread")
        return snapshot
