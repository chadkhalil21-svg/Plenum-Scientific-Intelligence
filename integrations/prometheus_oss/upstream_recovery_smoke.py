"""Focused offline evidence path check, using real upstream coordination and mock model transport."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import upstream_specialists as u

def main():
    mission,commitment=u.fixture("science")
    identity={"case":"offline-recovery"}
    md=u.mp.MODEL_DIGEST+"0"*52
    good={k:k in ("bibliography","stations") for k in mission["authorized_inputs"]}
    bad={k:k=="stations" for k in good}
    assert u.selection_matches(good,commitment) and not u.selection_matches(bad,commitment)
    assert u.mp.valid_digest(md)
    empty={k:False for k in good}
    assert not u.selection_matches(empty,u.mp.digest([]))
    for malformed in ({}, {**empty,"unauthorized":True}, {**empty,"stations":1}):
        try:u.validate_selection(mission,malformed)
        except ValueError:pass
        else:raise AssertionError("Malformed proposal accepted")
    try:u.vm.graph(mission,empty)
    except ValueError:pass
    else:raise AssertionError("Empty executable graph accepted")
    for label,answers,accepted in (("first-pass",[good,good],True),
                                   ("recovered",[bad,bad,good],True),
                                   ("rejected",[bad,bad,bad],False),
                                   ("empty-specialist",[empty,good],True),
                                   ("empty-peer-recovery",[empty,empty,good],True),
                                   ("empty-terminal-rejected",[empty,empty,empty],False)):
        requests=[u.vm.request(mission),u.peer_request(mission,answers[0])]
        if len(answers)==3:requests.append(u.correction_request(mission,answers[0],answers[1]))
        calls=[]
        def fake(path,request,timeout):
            i=len(calls)
            assert path=="/api/chat" and i<len(answers) and request==requests[i]
            calls.append(u.mp.digest(request))
            return {"model":u.mp.MODEL,"done":True,"eval_count":20,"prompt_eval_count":100,
                    "message":{"content":json.dumps(answers[i])}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"original"
            with patch.object(u.mp,"check_local_model",return_value=md),patch.object(u.mp,"read_json",side_effect=fake):
                if accepted:
                    proof=u.execute_bound(root,mission,commitment,identity)
                    assert proof["selection"]==good and proof["model_calls"]==len(answers)
                    assert proof.get("independent_rejection_recovered",False)==(len(answers)==3)
                else:
                    try:u.execute_bound(root,mission,commitment,identity)
                    except ValueError as exc:assert str(exc)=="Independent corrective selection rejected"
                    else:raise AssertionError("Rejected correction accepted")
                    assert not (root/"workflow-result.json").exists()
            assert len(calls)==len(answers)==len(set(calls))
            with patch.object(u.mp,"read_json",side_effect=AssertionError("Independent verifier called model")):
                if accepted:
                    assert u.verify_bound(root,mission,commitment,identity)==proof
                    if len(answers)==3:
                        f=root/"correction.result.json"
                        row=json.loads(f.read_text());row["answer"]=bad;f.write_text(json.dumps(row))
                    else:
                        (root/"correction.result.json").write_text("{}")
                    try:u.verify_bound(root,mission,commitment,identity)
                    except ValueError:pass
                    else:raise AssertionError("Unexpected or altered evidence accepted")
            print(label,"PASS (mock model transport only)")
if __name__=="__main__":main()
