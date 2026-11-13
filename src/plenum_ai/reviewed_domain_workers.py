"""Reuse ALREADY TESTED original public validators and primary sources.

Not another agent, framework, host, model or licensing intake. If the original
founder asks for a specifically supported Cloudflare Free neuron-budget
validator or NOAA CO-OPS station metadata validator, reuse the EXISTING
verified exact source code rather than emit the unrelated generic numeric
starter. Unknown goals keep the existing explicitly review-only starter path.
No credentials, billable inference, browser login, or account writes.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DOMAIN_SOURCES = {
    "cloudflare_workers_ai_free": (
        ("Cloudflare Workers AI neuron pricing", "Cloudflare",
         "https://developers.cloudflare.com/workers-ai/platform/pricing/"),
        ("Cloudflare Workers AI model free-tier restrictions", "Cloudflare",
         "https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/"),
    ),
    "noaa_water_station_metadata": (
        ("NOAA CO-OPS station metadata API documentation", "NOAA",
         "https://api.tidesandcurrents.noaa.gov/mdapi/dev/"),
    ),
}
DOMAIN_FILES = {
    "cloudflare_workers_ai_free": ROOT / "tools" / "cloudflare_workers_ai_budget.py",
    "noaa_water_station_metadata": ROOT / "tools" / "water_level_metadata.py",
}
MAX_SOURCE_BYTES = 40_000


def match_original_capability(objective: str) -> str | None:
    """Match narrow task semantics, NEVER model-generated filenames/paths."""
    if not isinstance(objective, str) or len(objective) > 120:
        return None
    value = " " + objective.lower().replace("-", " ") + " "
    if ("cloudflare" in value
        and ("workers ai" in value or "neuron" in value or "inference" in value)
        and any(x in value for x in ("validator", "budget", "usage", "validate"))):
        return "cloudflare_workers_ai_free"
    if ("noaa" in value
        and any(x in value for x in ("station", "water level", "co ops"))
        and any(x in value for x in ("metadata", "validator", "validation"))):
        return "noaa_water_station_metadata"
    return None


def _original_functional_test(capability: str) -> str:
    if capability == "cloudflare_workers_ai_free":
        return '''import unittest
from main import validate, REVIEWED

class ExistingSourceAcceptance(unittest.TestCase):
    def test_actual_free_budget_semantics(self):
        data = {
            "plan": "free",
            "model": "@cf/zai-org/glm-4.7-flash",
            "usage_day_utc": REVIEWED.isoformat(),
            "neurons_used_today": 9951,
            "neurons_reserved": 8,
            "input_tokens_upper_bound": 1000,
            "output_tokens_upper_bound": 1000,
        }
        self.assertEqual(validate(data, today=REVIEWED)["status"], "BLOCK")
        data["neurons_used_today"] = 9950
        v = validate(data, today=REVIEWED)
        self.assertEqual(v["local_remaining_after"], 0)
        self.assertFalse(v["account_plan_and_usage_verified"])
        self.assertFalse(v["zero_cost_guaranteed"])
        self.assertFalse(v["inference_executed"])

if __name__ == "__main__":
    unittest.main()
'''
    if capability == "noaa_water_station_metadata":
        return '''import unittest
from main import validate_station_metadata

class ExistingSourceAcceptance(unittest.TestCase):
    def test_real_noaa_station_metadata_structure(self):
        good = {"id": "9414290", "name": "San Francisco",
                "lat": 37.806, "lng": -122.465}
        report = validate_station_metadata({"stations": [good]})
        self.assertEqual(report["structurally_valid_rows"], 1)
        self.assertFalse(report["datum_reference_validated"])
        bad = validate_station_metadata({"stations": [dict(good, lat=999)]})
        self.assertEqual(bad["invalid_rows"], 1)
        self.assertEqual(bad["errors"][0]["code"], "invalid_latitude")

if __name__ == "__main__":
    unittest.main()
'''
    raise ValueError("Not a reviewed original first-party capability")


def reuse_original_program(capability: str, objective: str, output_dir: Path) -> dict:
    """Make a usable, independently checked copy of a reviewed original tool."""
    source = DOMAIN_FILES.get(capability)
    if source is None or not isinstance(objective, str):
        raise ValueError("Unapproved domain task")
    if (source.is_symlink() or not source.is_file()
            or source.stat().st_size > MAX_SOURCE_BYTES):
        raise ValueError("Existing reviewed source unavailable or unsafe")
    if output_dir.exists() and (output_dir.is_symlink() or any(output_dir.iterdir())):
        raise FileExistsError("Never overwrite prior source or work")
    code = source.read_bytes()
    ast.parse(code.decode("utf-8"), filename="main.py")
    test = _original_functional_test(capability)
    ast.parse(test, filename="test_generated.py")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "main.py").write_bytes(code)
    (output_dir / "test_generated.py").write_text(test, encoding="utf-8")
    references = DOMAIN_SOURCES[capability]
    (output_dir / "README.md").write_text(
        "# Existing verified Plenum public tool reused\n\n"
        + "Founder's objective: " + objective + "\n\n"
        + "Original source: " + source.relative_to(ROOT).as_posix() + "\n"
        + "Functional check: python -m unittest -v test_generated.py\n\n"
        + "\n".join(url for _, _, url in references)
        + "\n\nNo paid inference, live provider account proof, deployment "
          "or objective-level autonomous originality is claimed.\n", encoding="utf-8")
    check = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "test_generated.py"],
        cwd=output_dir, capture_output=True, text=True, timeout=12,
        check=False,
    )
    if check.returncode != 0 or "OK" not in check.stderr[-700:]:
        raise RuntimeError("Existing audited domain program failed its own real functional check")
    manifest = {
        "schema": "plenum-reviewable-program-v1",
        "kind": capability,
        "public_topic": objective,
        "file_count": 3,
        "main_sha256": sha256(code).hexdigest(),
        "reused_original_repo_source": source.relative_to(ROOT).as_posix(),
        "functional_verifier_executed_and_passed": True,
        "synthesis_method": "exact already-tested first-party original tool reuse; no model",
        "generated_program_has_not_been_deployed": True,
        "external_code_execution_approved": False,
        "human_code_review_required": True,
        "owner_review_required": True,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def official_source_records(capability: str, *, opener=urlopen) -> list[dict]:
    """Bounded live read-only GET of ONLY vetted first-party primary sources."""
    if capability not in DOMAIN_SOURCES:
        raise ValueError("Unknown reviewed domain reference set")
    records = []
    for title, organization, url in DOMAIN_SOURCES[capability]:
        request = Request(url, headers={"User-Agent": "PlenumOriginalMinisterPublicResearch/1"})
        try:
            with opener(request, timeout=15) as response:
                redirected = response.geturl()
                status = response.status
                # Never include HTML/page content in machine instructions,
                # repositories, model prompts or untrusted agent output.
                response.read(4096)
        except (OSError, TimeoutError, ValueError):
            continue
        if redirected != url or status != 200:
            continue
        records.append({"source": organization, "title": title, "url": url,
                        "http_status": status,
                        "independently_quoted_page_text": False})
    return records
