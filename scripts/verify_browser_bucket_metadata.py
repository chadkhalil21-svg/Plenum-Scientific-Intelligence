"""Validate *actual* gcloud storage bucket privacy metadata; no secrets emitted.

gcloud storage buckets describe uses normalized snake_case fields unless --raw
is requested. Do not confuse this with the Cloud Storage JSON API's nested
iamConfiguration camelCase representation. Accept both, fail closed.
"""
import json
import sys


def assert_private_bucket(data):
    if not isinstance(data, dict):
        raise ValueError("Missing Cloud Storage bucket metadata")
    iam = data.get("iamConfiguration") or data.get("iam_configuration") or data.get("iam_config") or {}
    pap = data.get("public_access_prevention")
    if pap is None:
        pap = iam.get("publicAccessPrevention", iam.get("public_access_prevention"))
    uniform = data.get("uniform_bucket_level_access")
    if uniform is None:
        uniform = iam.get("uniformBucketLevelAccess", iam.get("uniform_bucket_level_access"))
    if isinstance(uniform, dict):
        uniform = uniform.get("enabled")
    if pap != "enforced":
        raise ValueError("Browser storage requires enforced public-access prevention")
    if uniform is not True:
        raise ValueError("Browser storage requires uniform bucket-level IAM")
    return True


if __name__ == "__main__":
    try:
        assert_private_bucket(json.load(sys.stdin))
    except (ValueError, TypeError, KeyError) as exc:
        print(f"Private bucket policy verification FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Private browser bucket security verified (public access blocked; uniform IAM).")
