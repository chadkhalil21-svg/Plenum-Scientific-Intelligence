"""Real SQLite backup/restore and negative fixtures; no model or remote call."""
import json,os,sqlite3,tempfile
from pathlib import Path
from unittest.mock import patch
from snapshot import seal,restore,check_prefix,logical
with tempfile.TemporaryDirectory() as d:
    p=Path(d);src=p/"original";src.mkdir()
    with sqlite3.connect(src/"graph.sqlite") as c:
        c.execute("create table checkpoints (id text primary key, payload blob)")
        c.execute("insert into checkpoints values (?,?)",("thread",b"synthetic"))
    for name in ("pause.json","manifest.json","read_evidence.json"):
        (src/name).write_text('{"synthetic":true}')
    deps=p/"dependencies.txt";deps.write_text("synthetic==1\n")
    env={"GITHUB_ACTIONS":"true","GITHUB_RUN_ID":"123","GITHUB_SHA":"a"*40,"GITHUB_RUN_ATTEMPT":"1","GITHUB_JOB":"prepare","RUNNER_NAME":"synthetic-source"}
    with patch.dict(os.environ,env):
        seal(src,p/"backup",deps)
        with patch.dict(os.environ,{"GITHUB_JOB":"qualify"}):
            try:restore(p/"backup",p/"invalid",p/"invalid.json")
            except PermissionError:pass
            else:raise AssertionError("Same runner accepted")
        with patch.dict(os.environ,{"GITHUB_JOB":"qualify","RUNNER_NAME":"synthetic-destination"}):
            restore(p/"backup",p/"restored",p/"proof.json")
            assert logical(src/"graph.sqlite")==logical(p/"restored"/"graph.sqlite")
            check_prefix(p/"restored",p/"proof.json")
            (p/"restored"/"pause.json").write_text("{}")
            try:check_prefix(p/"restored",p/"proof.json")
            except ValueError:pass
            else:raise AssertionError("Changed prefix accepted")
            (p/"backup"/"graph"/"read_evidence.json").write_text("{}")
            try:restore(p/"backup",p/"tampered",p/"tampered.json")
            except ValueError:pass
            else:raise AssertionError("Tampered backup accepted")
print("PASS real SQLite backup, logical restore, distinct runner and immutable-prefix rejection fixtures")
