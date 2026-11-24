"""Bounded profile-specific work products inside native divisions, not 11 independent processes."""
from hashlib import sha256
from checkpoint_store import encoded
from mission_scope import PROFILE_DIVISIONS, digest

def hash_value(value):
    return sha256(encoded(value)).hexdigest()

def receipt(profile, scope, inputs, output):
    return {"profile":profile,"division":PROFILE_DIVISIONS[profile],
            "scope_sha256":digest(scope),"input_sha256":hash_value(inputs),
            "output":output,"output_sha256":hash_value(output),"paid_inference":False}

def chief_receipt(scope, plan):
    if len(set(plan["tasks"].values()))!=5 or len(plan["order"])!=5:
        raise ValueError("Chief requires five distinct assignments")
    return receipt("chief",scope,plan,{"native_parent":plan["parent"],
        "ordered_assignments":[{"division":r,"issue":plan["tasks"][r]} for r in plan["order"]]})

def division_receipts(role, scope, prior, result, directory):
    budget=scope["kind"]=="bibliography_budget"
    inputs={"prior":{k:hash_value(v) for k,v in prior.items()},"result":hash_value(result)}
    out={}
    def add(profile, value):
        if PROFILE_DIVISIONS[profile]!=role:raise ValueError("Wrong profile division")
        out[profile]=receipt(profile,scope,inputs,value)
    if role=="intelligence":
        # Actual approved API retrieval is performed by the original division.
        # This is a source-access receipt, never a graphical/browser login claim.
        if budget:
            identifiers=sorted(result)
        else:
            from plenum_ai.chief_team_mission import _station_rows
            ids=tuple(scope.get("station_ids",["8723214"]))
            identifiers=sorted(row["id"] for row in _station_rows(result,ids))
        add("browser",{"transport":"approved public provider API","provider":"Crossref" if budget else "NOAA",
                       "identifiers":identifiers,"interactive_browser_executed":False})
    elif role=="research":
        ids=sorted(scope["dois"]) if budget else sorted(result["readback"])
        add("research",{"bibliographic_identifiers":ids,"metadata_readback_sha256":hash_value(result),
                        "full_text_validation":False})
    elif role=="engineering":
        from pathlib import Path
        from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
        name=result["artifact_dir"]
        if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:
            raise ValueError("Unsafe profile artifact path")
        artifact=directory/name
        source=artifact/"main.py"
        if artifact.is_symlink() or source.is_symlink():
            raise ValueError("Unsafe profile source")
        data=source.read_bytes()
        original=DOMAIN_FILES["cloudflare_workers_ai_free" if budget else "noaa_water_station_metadata"]
        source_hash=sha256(data).hexdigest()
        if (data!=original.read_bytes() or source_hash!=result["manifest"]["main_sha256"]
                or result["manifest"]["functional_verifier_executed_and_passed"] is not True):
            raise ValueError("Coding source digest mismatch")
        add("coding",{"reviewed_source_sha256":source_hash,"functional_test_passed":
                      result["manifest"]["functional_verifier_executed_and_passed"],"deployed":False})
        if budget:
            from budget_mission import evaluate
            data=dict(result["input"])
            data["neurons_reserved"]=min(10000,data["neurons_reserved"]+1)
            observed=evaluate(source,data)
            add("simulation",{"scenario":"synthetic reserve increment","inputs":data,
                              "observed":observed,"physical_validation":False})
        else:
            from plenum_ai.chief_team_mission import _station_rows
            from math import radians,sin,cos,asin,sqrt
            ids=tuple(scope.get("station_ids",["8723214"]))
            rows=_station_rows(prior["intelligence"]["result"],ids)
            distances=[]
            for i,a in enumerate(rows):
                for b in rows[i+1:]:
                    p,q=radians(float(a["lat"])),radians(float(b["lat"]))
                    dl=radians(float(b["lng"])-float(a["lng"]))
                    h=sin((q-p)/2)**2+cos(p)*cos(q)*sin(dl/2)**2
                    distances.append({"pair":[a["id"],b["id"]],"distance_km":round(12742*asin(sqrt(min(1,max(0,h)))),6)})
            add("simulation",{"scenario":"spherical coordinate screening","pairs":distances,
                              "station_count":len(rows),"physical_validation":False})
    elif role=="commercial":
        recommendation=result["recommendation"]
        limitations=result["limitations"]
        subject="offline AI budget" if budget else "coastal metadata"
        add("operations",{"next_action":recommendation,"blocked_by":limitations,
                          "owner":"Scientific Research and Engineering","external_write":False})
        add("creative",{"format":"unpublished three-panel storyboard","panels":[
            {"heading":"Question","caption":result["objective"]},
            {"heading":"Evidence","caption":subject+" screening; "+str(len(limitations))+" stated limitations"},
            {"heading":"Next step","caption":recommendation}],"rendered_media":False})
        add("marketing",{"hypothesis":"A qualified audience may request a "+subject+" evidence review",
                          "experiment":"Founder-reviewed informational brief; no outreach",
                          "metric":"qualified review requests / approved brief recipients",
                          "baseline":None,"campaign_launched":False})
        add("support",{"draft":"Thank you for your interest. This review concerns "+subject+
            ". "+limitations[0]+". "+recommendation+".","sent":False})
    elif role=="verification":
        brief=prior["commercial"]["result"]
        add("verification",{"independent_actual_input_test":result["independent_actual_input_test"],
                            "verified_producers":result["verified_producers"],"provider_replay":False})
        add("business_advisor",{"alternatives":[{"action":"Proceed to bounded further review","condition":brief["recommendation"]},
                  {"action":"Defer external commitment","condition":"; ".join(brief["limitations"])}],
                  "recommended":"Further evidence review only","financial_commitment":False})
    else:raise ValueError("Unknown profile division")
    if set(out)!={p for p,r in PROFILE_DIVISIONS.items() if r==role}:raise ValueError("Profile coverage mismatch")
    return out
