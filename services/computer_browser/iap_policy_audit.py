"""Summarize exact resource-level IAM bindings without exposing other principals.

The caller acquires the IAM policies separately through read-only Google APIs.
Print only whether the two required resource-specific grants are present.
Do not infer effective access from an absent *project-level* binding.
"""
import argparse
import json
from pathlib import Path

IAP_ROLE = "roles/iap.httpsResourceAccessor"
INVOKER_ROLE = "roles/run.invoker"
DEPLOYER = "plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com"

def policy_grant(policy, role, principal):
    """True only for an unconditional, exact binding; False if absent.

    Conditional grants are not treated as always available.
    """
    if not isinstance(policy, dict):
        raise ValueError("IAM policy is not an object")
    matches = [b for b in policy.get("bindings", [])
               if isinstance(b, dict) and b.get("role") == role
               and principal in b.get("members", [])]
    if not matches:
        return "no_explicit_binding"
    if any(not b.get("condition") for b in matches):
        return "explicit_unconditional_binding"
    return "explicit_conditional_binding"

def summary(iap_policy, run_policy, project_number):
    if not isinstance(project_number, str) or not project_number.isdecimal():
        raise ValueError("Project number must be decimal")
    agent = f"service-{project_number}@gcp-sa-iap.iam.gserviceaccount.com"
    return {
        "schema": "plenum-iap-resource-permissions-v1",
        "iap_policy_read": iap_policy is not None,
        "run_service_policy_read": run_policy is not None,
        "deployer_iap_access_binding": (
            policy_grant(iap_policy, IAP_ROLE, "serviceAccount:" + DEPLOYER)
            if iap_policy is not None else "unavailable"),
        "iap_service_agent_run_invoker_binding": (
            policy_grant(run_policy, INVOKER_ROLE, "serviceAccount:" + agent)
            if run_policy is not None else "unavailable"),
        "permission_changes": False,
        "authentication_test_performed": False,
        "caution": "Absence of an explicit resource binding does not rule out inherited access.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--iap-policy")
    p.add_argument("--run-policy")
    p.add_argument("--project-number", required=True)
    a = p.parse_args()
    def read_json(path):
        return json.loads(Path(path).read_text(encoding="utf-8")) if path else None
    print(json.dumps(summary(read_json(a.iap_policy), read_json(a.run_policy),
                             a.project_number), sort_keys=True))

if __name__ == "__main__":
    main()
