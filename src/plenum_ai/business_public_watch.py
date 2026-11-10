"""Public business endpoint readback with bounded recovery; no credentials or writes."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

@dataclass(frozen=True)
class Target:
    name: str
    url: str
    kind: str

# Public Render URLs independently observed from the connected Render inventory.
TARGETS = (
    Target("corporate", "https://american-rider-corporate.onrender.com/", "html"),
    Target("platform", "https://american-rider-platform.onrender.com/", "html"),
    Target("public_server", "https://american-rider-server-3d7x.onrender.com/health", "health"),
)

class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def probe(target: Target, *, opener=None, timeout: int = 12) -> tuple[bool, str, int | None]:
    """Only exact hardcoded public HTTPS URLs; return a small status, never page content."""
    client = opener or build_opener(NoRedirects)
    req = Request(target.url, headers={
        "Accept": "application/json" if target.kind == "health" else "text/html",
        "User-Agent": "PlenumPublicOpsReadback/1",
    }, method="GET")
    try:
        with client.open(req, timeout=timeout) as resp:
            code = resp.status
            if code != 200:
                return False, "non_200_http", code
            ct = resp.headers.get("Content-Type", "").lower()
            if target.kind == "health":
                if "json" not in ct:
                    return False, "unexpected_content_type", code
                data = json.loads(resp.read(65537))
                if not isinstance(data, dict) or data.get("service") != "american-rider-server":
                    return False, "unexpected_service", code
            elif "html" not in ct:
                return False, "unexpected_content_type", code
            return True, "verified_read", code
    except HTTPError as exc:
        return False, "non_200_http", int(exc.code)
    except (URLError, TimeoutError, ConnectionError, OSError):
        return False, "network_unverified", None
    except (ValueError, UnicodeError, TypeError):
        return False, "unexpected_content", None

def inspect_target(target: Target, *, probe_fn=probe, sleep_fn=time.sleep,
                   max_attempts: int = 3) -> dict:
    """Require two fresh successful GETs, bounded retry per independent pass."""
    if max_attempts not in (1, 2, 3):
        raise ValueError("attempt count must be 1..3")
    attempts = 0
    evidence = []
    for phase in ("initial", "readback"):
        ok = False
        for n in range(max_attempts):
            attempts += 1
            passed, reason, code = probe_fn(target)
            if passed:
                evidence.append({"phase": phase, "http": code, "result": "verified_read"})
                ok = True
                break
            if n + 1 < max_attempts:
                sleep_fn(min(2 ** n, 4))
        if not ok:
            return {"service": target.name, "status": "UNVERIFIED",
                    "phase": phase, "attempts": attempts, "reason": reason,
                    "http": code, "external_actions_executed": False}
    return {"service": target.name, "status": "PUBLIC_HTTP_VERIFIED",
            "independent_gets": len(evidence), "attempts": attempts,
            "http": 200, "external_actions_executed": False}

def run(probe_fn=probe, sleep_fn=time.sleep, targets=TARGETS) -> dict:
    reports = [inspect_target(t, probe_fn=probe_fn, sleep_fn=sleep_fn) for t in targets]
    return {
        "schema": "plenum-public-business-readback-v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "public_https_read_only",
        "verified": sum(x["status"] == "PUBLIC_HTTP_VERIFIED" for x in reports),
        "total": len(reports), "reports": reports,
        "asserts_commercial_readiness": False, "asserts_transaction_success": False,
        "requires_production_credentials": False,
    }

def main():
    p = argparse.ArgumentParser(description="Public read-only business availability monitor")
    p.add_argument("--out", default="reports/public-business-readback.json")
    args = p.parse_args()
    out = Path(args.out)
    if (out.is_absolute() or ".." in out.parts or not out.parts
            or out.parts[0] != "reports" or out.suffix != ".json"):
        raise SystemExit("Report path must be a relative JSON under reports/")
    result = run()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PUBLIC_BUSINESS_READBACK {result['verified']}/{result['total']} public endpoints independently reread")
    for row in result["reports"]:
        print(f"{row['service']} {row['status']} attempts={row['attempts']} reason={row.get('reason', 'ok')}")
    if result["verified"] != result["total"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
