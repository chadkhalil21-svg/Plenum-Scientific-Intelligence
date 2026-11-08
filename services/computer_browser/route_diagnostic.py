"""Read-only, redacted diagnosis of Google Cloud Run 404 responses.

This only interprets service metadata returned by a trusted gcloud client.
No IAM modification, public URL enabling, private account data or token reads.
"""
import json
from pathlib import Path

SERVICE = "plenum-computer-browser"

def describe_route(service):
    if not isinstance(service, dict):
        raise ValueError("Cloud Run metadata must be a JSON object")
    meta = service.get("metadata") or {}
    status = service.get("status") or {}
    if meta.get("name") != SERVICE:
        raise ValueError("Unexpected Cloud Run service")
    annotations = meta.get("annotations") or {}
    ingress = annotations.get("run.googleapis.com/ingress") or service.get("ingress") or "not reported"
    disabled = annotations.get("run.googleapis.com/default-url-disabled")
    if disabled is None:
        disabled = service.get("defaultUriDisabled")
    if isinstance(disabled, str):
        disabled = disabled.strip().lower() == "true"
    ready = None
    for cond in status.get("conditions") or []:
        if cond.get("type") == "Ready":
            ready = str(cond.get("status")).lower() == "true"
            break
    url = status.get("url") or service.get("uri") or ""
    if not isinstance(url, str):
        url = ""
    url_ok = url.startswith("https://") and url.endswith(".run.app") and SERVICE in url
    restricted = ingress in (
        "internal", "internal-and-cloud-load-balancing",
        "INGRESS_TRAFFIC_INTERNAL_ONLY", "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER")
    if disabled is True:
        lead = "default_run_app_url_disabled"
    elif restricted:
        lead = "external_github_runner_may_be_blocked_by_ingress"
    elif ready is False:
        lead = "service_not_ready"
    elif not url_ok:
        lead = "service_url_missing_or_unexpected"
    else:
        lead = "404_not_explained_by_reported_route_metadata"
    return {
        "schema": "plenum-browser-route-diagnostic-v1",
        "service_matches": True,
        "cloud_run_url_format_expected": url_ok,
        "ingress_mode": str(ingress)[:75],
        "default_run_app_url_disabled": bool(disabled) if disabled is not None else None,
        "service_ready": ready,
        "possible_cause": lead,
        "iap_permissions_changed": False,
        "ingress_changed": False,
        "authenticated_browser_actions_enabled": False,
    }


def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    print(json.dumps(describe_route(data), sort_keys=True))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("metadata_json")
    main(p.parse_args().metadata_json)
