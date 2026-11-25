"""Regression for actual WAL-mode backup layout and strict restore rejection."""
import json,os,shutil,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from snapshot import seal,restore,logical,manifest,check_prefix

def main():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);source=p/"source";source.mkdir()
        (source/"pause.json").write_text('{"acknowledged":true}')
        (source/"manifest.json").write_text('{"paid_inference":false}')
        (source/"model-01.reserved.json").write_text('{"request_sha256":"test"}')
        (source/"model-01.result.json").write_text('{"completed":true}')
        (source/"read_evidence.json").write_text('{"completed":true}')
        deps=p/"deps.txt";deps.write_text("example==1\n")
        env={"GITHUB_ACTIONS":"true","GITHUB_RUN_ID":"123","GITHUB_SHA":"a"*40,"GITHUB_RUN_ATTEMPT":"1","GITHUB_JOB":"prepare","RUNNER_NAME":"synthetic-source"}
        with closing(sqlite3.connect(source/"graph.sqlite")) as db:
            assert db.execute("PRAGMA journal_mode=WAL").fetchone()==("wal",)
            db.execute("create table checkpoints (id integer primary key, body text)")
            db.execute("insert into checkpoints values (1,'acknowledged')");db.commit()
            assert (source/"graph.sqlite-wal").stat().st_size>0
            with patch.dict(os.environ,env):
                seal(source,p/"sealed",deps)
            original=logical(source/"graph.sqlite")
        backup=p/"sealed";row=json.loads((backup/"backup.json").read_text())
        assert row["source_logical_sha256"]==original
        assert set(row["files"])==set(manifest(backup/"graph"))
        assert not any(n.endswith(("-wal","-shm","-journal")) for n in row["files"])
        with patch.dict(os.environ,{**env,"GITHUB_JOB":"qualify","RUNNER_NAME":"synthetic-target"}):
            proof=p/"restore.json";dest=p/"restored"
            restore(backup,dest,proof)
            assert logical(dest/"graph.sqlite",sealed=True)==original
            assert check_prefix(dest,proof)["model_calls_replayed"]==0
            for label in ("sidecar","nested","symlink","traversal","absolute","tamper","rootlink","ancestorlink"):
                bad=p/("bad-"+label);shutil.copytree(backup,bad)
                graph=bad/"graph"
                if label=="sidecar":(graph/"graph.sqlite-wal").write_bytes(b"")
                elif label=="nested":(graph/"nested").mkdir()
                elif label=="symlink":(graph/"pause.json").unlink();(graph/"pause.json").symlink_to(source/"pause.json")
                elif label in ("traversal","absolute"):
                    v=json.loads((bad/"backup.json").read_text());v["files"]["../pause.json" if label=="traversal" else "/tmp/pause.json"]=v["files"]["pause.json"];(bad/"backup.json").write_text(json.dumps(v))
                elif label=="tamper":(graph/"pause.json").write_text("{}")
                elif label=="rootlink":
                    shutil.rmtree(graph);graph.symlink_to(backup/"graph",target_is_directory=True)
                elif label=="ancestorlink":
                    link=p/"ancestor";link.symlink_to(p,target_is_directory=True);bad=link/bad.name
                target=p/("rejected-"+label);receipt=p/("rejected-"+label+".json")
                try:restore(bad,target,receipt)
                except (ValueError,PermissionError):pass
                else:raise AssertionError("Invalid checkpoint accepted: "+label)
                assert not target.exists() and not receipt.exists()
    print("PASS: real WAL-backed SQLite snapshot; canonical standalone restore; eight unsafe tree/path/byte rejection fixtures")
if __name__=="__main__":main()
