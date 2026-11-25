"""Read-only exact-baseline source integrity audit; no inference or external effects."""
import hashlib, json, pathlib, subprocess
BASE = "5741225d746a0f456f9166baf2ce815a08b99fd6"
SPECS = {
  "integrations/paperclip/sequential_mission.py": "9d5688c675ce13b371a714396043cc3779e90e19",
  "integrations/paperclip/fresh_runner_acceptance.py": "2f906656f8c5ce083a5d7739e62dff08553e184c",
  "integrations/paperclip/objective_mission.py": "7f46c55776de627fc41e986c7d87e08705a7213b",
  "integrations/paperclip/dataset_mission.py": "6cdfe087e715b4831c8c03bfcc8900aeba6ccbfd",
  "integrations/paperclip/budget_mission.py": "2978f7c839128d78bd324c0653d9441f81cdc6d2",
  "src/plenum_ai/chief_contract_plan.py": "1af08d417bdffa064efe55e0233547927bf1ce18",
  "src/plenum_ai/reviewed_domain_workers.py": "827aeab3ba301f43c72ea725aa6cbe24488a6bcf",
  "src/plenum_ai/chief_team_mission.py": "2528cc4610a88300333597873521c336cf4c54d7",
  "integrations/prometheus_durability/receipts.py": "04ff93da10c614e00d4e6c7bd38d70610389c9e4"
}

def main():
    report = []
    for path, expected in SPECS.items():
        data = subprocess.check_output(["git", "show", BASE + ":" + path])
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()
        if digest != expected:
            raise ValueError((path, digest, expected))
        report.append(dict(path=path, bytes=len(data), git_blob_sha1=digest, sha256=hashlib.sha256(data).hexdigest()))
    print(json.dumps(dict(commit=BASE, files=report, paid_inference=False, replayed_calls=0, functional_qualification=False), indent=2))

if __name__ == "__main__":
    main()
