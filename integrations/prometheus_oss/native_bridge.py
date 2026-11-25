"""Native commercial division bridge: original adaptive commitment + OSS graph.

Only synthetic CI scope. The existing verified Engineering and Research results
are the input, and the native verification division reruns all checks without
inference. No replacement of the existing hidden-answer contract.
"""
import sys,os
from pathlib import Path
from checkpoint_store import checked,exclusive
from mission_scope import digest as scope_digest

def apply(scope,prior,directory,adaptive,*,execute):
    if os.getenv("GITHUB_ACTIONS")!="true":raise PermissionError("OSS native qualification is synthetic CI only")
    # Fixed reviewed dependency directory in the native Debian container.
    deps=Path("/opt/plenum-oss-deps")
    if deps.is_dir():sys.path.insert(0,str(deps))
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from harness import validate_input,execute as run,verify,digest
    from adaptive_turns import binding
    ident=binding(scope,directory)
    eng=prior["engineering"]["result"]
    spec=scope["inputs"]["synthesis"]["followup"]
    ctx=validate_input(eng["input"],eng["validation"],spec["budget"],spec["cost_per_review"])
    root=directory/"oss-graph"
    expected={**ident,"scope_sha256":scope_digest(scope),"upstream_sha256":digest(eng),"adaptive_sha256":digest(adaptive)}
    if execute and not root.exists():
        root.mkdir(mode=0o700)
        exclusive(root/"native-binding.json",expected)
        run(root,ctx,ident["parent"],"run")
    if checked(root/"native-binding.json",expected)!=expected:raise ValueError("Native graph identity changed")
    proof=verify(root,ctx,ident["parent"],adaptive["action"])
    if proof["paid_inference"] is not False or proof["model_calls_replayed"]!=0 or proof["provider_calls_replayed"]!=0:raise ValueError("OSS replay/cost gate")
    return {**proof,"native_paperclip_integration_verified":True,"native_binding_sha256":digest(expected),
        "original_adaptive_commitment_verified":True}
