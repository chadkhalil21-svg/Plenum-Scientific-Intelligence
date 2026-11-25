"""Two opposite holdout decisions; mocked transport only, no live inference claim."""
from copy import deepcopy
import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from checkpoint_store import exclusive
from mission_scope import digest as scope_digest,validate_scope
from synthesis_smoke import scope as synthesis_scope,fixture_selection
from synthesis_contract import accept_choice,independent as synth_independent
from adaptive_turns import digest,context,request,tool,independent,execute,verify

def scope(case):
    if case not in ("adaptive-review","adaptive-defer"):raise ValueError("Unknown fixture")
    s=synthesis_scope()
    # Synthesis comparison order is determined by the candidate IDs, not model order.
    data=accept_choice(s,fixture_selection(s))
    result=synth_independent(data)
    # This fixture independently knows exactly one disputed requirement: alarm.
    assert [r["attribute"] for r in result["comparisons"]]==["mode","material"]
    action="review" if case=="adaptive-review" else "defer"
    s["inputs"]["synthesis"]["followup"]={"objective":"Select conflicting requirements for review, calculate review cost, and decide whether the review fits the budget.",
        "cost_per_review":75,"budget":100 if action=="review" else 50,
        "commitment":digest({"selected":["review_1"],"review_cost":75,"action":action})}
    return validate_scope(s)

def smoke():
    for case in ("adaptive-review","adaptive-defer"):
        s=scope(case);d=accept_choice(s,fixture_selection(s));v=synth_independent(d)
        prior={"engineering":{"result":{"input":d,"validation":v}},"research":{"source":"fixture"}}
        ctx=context(s,prior);select={"review_1":True,"review_2":False}
        result=tool(ctx,select);decision={"action":"review" if case=="adaptive-review" else "defer"}
        expected=independent(ctx,select,decision,s["inputs"]["synthesis"]["followup"]["commitment"])
        assert request(ctx,1)!=request(ctx,2,result)
        assert s["inputs"]["synthesis"]["followup"]["commitment"] not in json.dumps(request(ctx,2,result))
        for bad_select,bad_decision in [({"review_1":False,"review_2":True},decision),(select,{"action":"no_review"})]:
            try:independent(ctx,bad_select,bad_decision,s["inputs"]["synthesis"]["followup"]["commitment"])
            except ValueError:pass
            else:raise AssertionError("Invalid decision accepted")
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);cid,mid,iid=map(str,(uuid4(),uuid4(),uuid4()));sha=scope_digest(s)
            exclusive(p/"prepared.json",{"schema":"plenum-prepared-mission-v1","company":cid,"mission":mid,"scope_sha256":sha,"checkpoint_mode":"local","model_mode":"local"})
            exclusive(p/"activation.json",{"company":cid,"mission":mid,"scope_sha256":sha,"model_mode":"local"})
            exclusive(p/"minister-plan.json",{"company":cid,"parent":mid,"scope_sha256":sha,"tasks":{"commercial":iid}})
            calls=[]
            def fake(path,payload,timeout):
                calls.append(payload)
                return {"done":True,"model":"qwen3.5:4b","message":{"content":json.dumps(select if len(calls)==1 else decision)},"eval_count":12}
            with patch("model_plan.check_local_model",return_value="d8b0f5e9760c"+"0"*52),patch("model_plan.read_json",side_effect=fake):
                row=execute(s,prior,p);assert len(calls)==2 and row["action"]==expected["action"]
                assert execute(s,prior,p)==row and verify(s,prior,p)==row and len(calls)==2
                assert calls[1]==request(ctx,2,result)
                # A missing turn receipt after a reserved call cannot cause replay.
                (p/"adaptive-turn-2.json").unlink()
                try:execute(s,prior,p)
                except ValueError:pass
                else:raise AssertionError("Ambiguous turn accepted")
                assert len(calls)==2
    print("PASS: outcome-dependent turn chaining, two distinct budget decisions, hidden commitment, immutable reservation and zero replay fixtures")

if __name__=="__main__":
    if len(sys.argv)==2:print(json.dumps(scope(sys.argv[1]),separators=(",",":")))
    else:smoke()
