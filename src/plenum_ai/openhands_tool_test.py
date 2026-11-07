"""Exercise a *real* pinned OpenHands editor executor in an ephemeral workspace.

This is a functional SDK tool test, not autonomous programming or a language
model evaluation. No agent, LLM, shell, internet, repo write, or private IP.
"""
import argparse
import ast
import importlib.metadata
import json
from pathlib import Path
import socket
import tempfile
from unittest.mock import patch

SDK_VERSION="1.60.1"
SCHEMA="plenum-openhands-tool-functional-v1"
START="def square(x):\n    return x + x\n"
FIXED="def square(x):\n    return x * x\n"

def plan():
    return {
        "schema":SCHEMA,
        "upstream":"OpenHands/software-agent-sdk",
        "sdk_version":SDK_VERSION,
        "sandbox":"ephemeral-temp-directory",
        "tool":"FileEditorExecutor",
        "tool_execution_verified":False,
        "unauthorized_write_blocked":False,
        "generated_code_executed":False,
        "agent_executed":False,
        "inference_calls":0,
        "external_api_calls":0,
        "private_data_used":False,
        "AGI_demonstrated":False,
    }

def _no_network(*_args,**_kwargs):
    raise RuntimeError("Outbound network forbidden in OpenHands offline test")

def run():
    """Verify editor create/edit/deny using official OpenHands action classes."""
    installed=importlib.metadata.version("openhands-sdk")
    if installed!=SDK_VERSION:
        raise RuntimeError("OpenHands SDK version not reviewed")
    from openhands.tools.file_editor import FileEditorAction, FileEditorExecutor

    with tempfile.TemporaryDirectory(prefix="plenum-oh-") as work:
        root=Path(work).resolve()
        approved=root/"toy.py"
        unapproved=root/"denied.py"
        editor=FileEditorExecutor(
            workspace_root=str(root),
            allowed_edits_files=[str(approved)],
        )
        with patch.object(socket.socket,"connect",_no_network):
            created=editor(FileEditorAction(
                command="create",path=str(approved),file_text=START))
            if created.is_error or approved.read_text()!=START:
                raise RuntimeError("OpenHands did not create the approved synthetic file")
            edited=editor(FileEditorAction(
                command="str_replace",path=str(approved),
                old_str="    return x + x",new_str="    return x * x"))
            if edited.is_error or approved.read_text()!=FIXED:
                raise RuntimeError("OpenHands did not repair the approved synthetic file")
            denied=editor(FileEditorAction(
                command="create",path=str(unapproved),
                file_text="PRIVATE = 'should never be written'\n"))
            if not denied.is_error or unapproved.exists():
                raise RuntimeError("OpenHands allowed a non-allowlisted file write")

        tree=ast.parse(approved.read_text())
        if (len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef)
            or tree.body[0].name!="square" or
            not isinstance(tree.body[0].body[0],ast.Return) or
            not isinstance(tree.body[0].body[0].value,ast.BinOp) or
            not isinstance(tree.body[0].body[0].value.op,ast.Mult)):
            raise RuntimeError("Resulting reviewed program AST differs from expected repair")
        return {
            **plan(),
            "tool_execution_verified":True,
            "authorized_create_and_edit":True,
            "unauthorized_write_blocked":True,
            "syntax_verified":True,
            "output_content_matches_reviewed_fixture":True,
            "workspace_deleted_on_exit":True,
            "agent_executed":False,
            "generated_code_executed":False,
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--execute",action="store_true")
    p.add_argument("--out",default="reports/openhands-tool-functional.json")
    args=p.parse_args()
    output=Path(args.out)
    if (output.is_absolute() or ".." in output.parts or output.suffix!=".json"
        or not output.parts or output.parts[0]!="reports" or len(output.parts)>4):
        raise ValueError("Only bounded JSON files inside reports/ allowed")
    report=run() if args.execute else plan()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("OpenHands sandbox tool functional:",report["tool_execution_verified"])

if __name__=="__main__":
    main()
