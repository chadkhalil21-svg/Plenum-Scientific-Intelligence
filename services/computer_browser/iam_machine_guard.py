"""Fail-closed verification for separate Cloud Run IAM-only machine smoke service.

No Google credentials are handled in this Python module. It validates metadata,
service-local bindings and a health response after the trusted GitHub job has
made minimal service-level API calls.
"""
import json
import re
from pathlib import Path

PROJECT = "plenum-computer-browser"
SERVICE = "plenum-computer-browser-machine"
REGION = "us-east1"
DEPLOYER = f"plenum-browser-deploy@{PROJECT}.iam.gserviceaccount.com"
RUNTIME = f"plenum-browser-machine-runtime@{PROJECT}.iam.gserviceaccount.com"
IMAGE = ("us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/"
         "computer-browser@sha256:"
         "a44497b72bc5ace7492838caf9dffb6c0559d985537774997884317b9519bbd0")


def verify_service(metadata, expected_image=IMAGE, public_read_enabled=False):
    image_prefix = ("us-east1-docker.pkg.dev/plenum-computer-browser/"
                    "plenum-browser/computer-browser@sha256:")
    if not (isinstance(expected_image, str)
            and expected_image.startswith(image_prefix)
            and re.fullmatch(r"[a-f0-9]{64}", expected_image[len(image_prefix):])):
        raise ValueError("Machine image must be immutable and from approved registry")
    if not isinstance(metadata, dict):
        raise ValueError("Invalid Cloud Run metadata")
    m = metadata.get("metadata") or {}
    spec = metadata.get("spec") or {}
    status = metadata.get("status") or {}
    template = spec.get("template") or {}
    inner = template.get("spec") or {}
    containers = inner.get("containers") or []
    if (m.get("name") != SERVICE or len(containers) != 1 or
        inner.get("serviceAccountName") != RUNTIME or
        containers[0].get("image") != expected_image):
        raise ValueError("Unexpected machine-only service identity, runtime or image")
    if any(v.get("name") in ("COMPUTER_BROWSER_TOKEN", "BROWSER_SESSION_KEY",
                            "BROWSER_PROFILE_BUCKET") or v.get("valueFrom")
           for v in containers[0].get("env", [])):
        raise ValueError("Machine smoke service must not receive website session secrets")
    environment = containers[0].get("env", [])
    if not isinstance(environment, list) or any(not isinstance(v, dict) for v in environment):
        raise ValueError("Invalid machine environment")
    settings = {v.get("name"): v.get("value") for v in environment}
    expected_env = {"BROWSER_ALLOWED_ORIGINS": "https://example.com"}
    if public_read_enabled is True:
        expected_env["MACHINE_IAM_PUBLIC_READ"] = "true"
    elif public_read_enabled is not False:
        raise ValueError("Invalid browser activation flag")
    if len(environment) != len(expected_env) or settings != expected_env:
        raise ValueError("Machine environment may only expose the exact approved public fixture mode")
    annotations = m.get("annotations") or {}
    if (annotations.get("run.googleapis.com/iap-enabled", "false").lower() == "true"
        or annotations.get("run.googleapis.com/invoker-iam-disabled", "false").lower() == "true"):
        raise ValueError("IAP or disabled Invoker IAM check detected")
    url = status.get("url", "")
    if not isinstance(url, str) or not re.fullmatch(
        r"https://plenum-computer-browser-machine-[a-z0-9.-]+[.]run[.]app", url):
        raise ValueError("Unexpected machine service URL")
    return url


def verify_service_iam(policy):
    if not isinstance(policy, dict):
        raise ValueError("Missing service IAM policy")
    invokers = set()
    for binding in policy.get("bindings", []):
        if not isinstance(binding, dict):
            raise ValueError("Invalid IAM binding")
        members = set(binding.get("members", []))
        if "allUsers" in members or "allAuthenticatedUsers" in members:
            raise ValueError("Public or overly broad Cloud Run policy")
        if binding.get("role") == "roles/run.invoker":
            if binding.get("condition"):
                raise ValueError("Unexpected conditional invocation grant")
            invokers.update(members)
    if invokers != {"serviceAccount:" + DEPLOYER}:
        raise ValueError("Only the existing GitHub deployer may invoke smoke service")
    return True


def verify_health(value):
    return (isinstance(value, dict)
            and value.get("service") == "plenum-computer-browser"
            and value.get("ready") is True
            and value.get("remote_mutations_enabled") is False)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--service-metadata", required=True)
    p.add_argument("--service-iam", required=True)
    p.add_argument("--health", required=True)
    p.add_argument("--anonymous-status", type=int, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    verify_service_iam(read(a.service_iam))
    verify_service(read(a.service_metadata))
    if a.anonymous_status == 200 or a.anonymous_status < 300:
        raise ValueError("Anonymous Cloud Run request was not denied")
    if not verify_health(read(a.health)):
        raise ValueError("Signed health response was not the expected application")
    print("PASS: IAM-only machine health authenticated; anonymous access rejected.")
    print("Existing owner IAP service was not changed; no website task was run.")


if __name__ == "__main__":
    main()
