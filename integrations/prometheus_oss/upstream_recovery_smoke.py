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
    for label,answers,accepted in (("first-pass",[good,good],True),
                                   ("recovered",[bad,bad,good],True),
                                   ("rejected",[bad,bad,bad],False)):
        requests=[u.vm.request(mission),u.peer_request(mission,answers[0])]
        if len(answers)==3:requests.append(u.correction_request(mission,answers[0],answers[1]))
        calls=[]
        def fake(path,request,timeout):
            i=len(calls)
            assert path=="/api/chat" and i<len(answers) and request==requests[i]
            calls.append(u.mp.digest(request))
            message={"content":json.dumps(answers[i])}
            if request["think"]:
                assert request["options"]["num_predict"]==1024 and timeout==360 and "format" not in request
                message["thinking"]="Mock deliberation; never archive this field"
            return {"model":u.mp.MODEL,"done":True,"done_reason":"stop","eval_count":20,"prompt_eval_count":100,
                    "message":message}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"original"
            with patch.object(u.mp,"check_local_model",return_value=md),patch.object(u.mp,"read_json",side_effect=fake):
                if accepted:
                    proof=u.execute_bound(root,mission,commitment,identity)
                    assert proof["selection"]==good and proof["model_calls"]==len(answers)
                    assert proof.get("independent_rejection_recovered",False)==(len(answers)==3)
                    assert proof["native_thinking_stages"]==(["peer","correction"] if len(answers)==3 else ["peer"])
                    assert all("Mock deliberation" not in p.read_text() for p in root.glob("*.json"))
                else:
                    try:u.execute_bound(root,mission,commitment,identity)
                    except ValueError as exc:assert str(exc)=="Independent corrective selection rejected"
                    else:raise AssertionError("Rejected correction accepted")
                    assert not (root/"workflow-result.json").exists()
            assert len(calls)==len(answers)==len(set(calls))
            with patch.object(u.mp,"read_json",side_effect=AssertionError("Independent verifier called model")):
                if accepted:
                    assert u.verify_bound(root,mission,commitment,identity)==proof
                    # Demonstrate old archives are still verified from exact legacy digests.
                    old_req=u.peer_request(mission,answers[0],reasoning=False)
                    for suffix in ("reserved","result"):
                        f=root/("peer."+suffix+".json")
                        old=json.loads(f.read_text());old["request_sha256"]=u.mp.digest(old_req)
                        old.pop("native_thinking_observed",None);f.write_text(json.dumps(old))
                    legacy_proof=u.verify_bound(root,mission,commitment,identity)
                    assert "peer" not in legacy_proof.get("native_thinking_stages",[])
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
