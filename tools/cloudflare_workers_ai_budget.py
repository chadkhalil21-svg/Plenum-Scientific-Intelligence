"""Fail-closed OFFLINE Cloudflare Workers AI Free neuron budget preflight.

Official sources, checked 2026-11-13 UTC:
https://developers.cloudflare.com/workers-ai/platform/pricing/
https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/
Rates are neurons per million input/output tokens. Free allocation is
10,000 neurons/day resetting 00 UTC; some models require paid access.
THIS IS NOT LIVE USAGE, ACCOUNT ENTITLEMENT OR ZERO-CHARGE GUARANTEE.
No network, account credentials, AI calls, or writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date, timezone
import json
from pathlib import Path

FREE_NEURONS = 10_000
REVIEWED = date(2026, 11, 13)
MODELS = {
    "@cf/zai-org/glm-4.7-flash": (5500, 36400),
    "@cf/google/gemma-4-26b-a4b-it": (9091, 27273),
    "@cf/nvidia/nemotron-3-120b-a12b": (45455, 136364),
}


def _count(data: dict, key: str, maximum: int) -> int:
    value = data.get(key)
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("invalid_" + key)
    return value


def validate(data: object, today: date | None = None) -> dict:
    current = today if today is not None else datetime.now(timezone.utc).date()
    def blocked(reason: str) -> dict:
        return {
            "schema": "plenum-workers-ai-free-preflight-v1",
            "status": "BLOCK",
            "reason": reason,
            "account_plan_and_usage_verified": False,
            "inference_executed": False,
            "zero_cost_guaranteed": False,
        }
    if not isinstance(data, dict):
        return blocked("invalid_input")
    if data.get("plan") != "free":
        return blocked("plan_not_declared_free")
    if current < REVIEWED or (current - REVIEWED).days > 30:
        return blocked("official_model_pricing_review_expired")
    if data.get("usage_day_utc") != current.isoformat():
        return blocked("stale_or_future_utc_usage")
    model = data.get("model")
    if not isinstance(model, str) or model not in MODELS:
        return blocked("model_not_confirmed_free")
    try:
        used = _count(data, "neurons_used_today", FREE_NEURONS)
        reserved = _count(data, "neurons_reserved", FREE_NEURONS)
        upper_input = _count(data, "input_tokens_upper_bound", 1_000_000)
        upper_output = _count(data, "output_tokens_upper_bound", 1_000_000)
    except ValueError as exc:
        return blocked(str(exc))
    if not upper_input or not upper_output:
        return blocked("positive_token_upper_bounds_required")
    inp, out = MODELS[model]
    estimate = (inp * upper_input + out * upper_output + 999_999) // 1_000_000
    remaining = max(0, FREE_NEURONS - used - reserved)
    if estimate > remaining:
        return {**blocked("estimated_request_exceeds_free_balance"),
                "estimate_neurons": estimate, "local_remaining_neurons": remaining}
    return {
        "schema": "plenum-workers-ai-free-preflight-v1",
        "status": "LOCAL_BUDGET_ESTIMATE_ONLY_ACCOUNT_UNVERIFIED",
        "model": model, "usage_day_utc": current.isoformat(),
        "estimate_neurons": estimate, "free_neurons_per_day": FREE_NEURONS,
        "local_remaining_before": remaining,
        "local_remaining_after": remaining - estimate,
        "account_plan_and_usage_verified": False,
        "inference_executed": False,
        "zero_cost_guaranteed": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_json", type=Path)
    args = p.parse_args()
    try:
        if (not args.input_json.is_file() or
                args.input_json.stat().st_size > 8192):
            raise ValueError("unsafe_input_size")
        result = validate(json.loads(args.input_json.read_text("utf-8")))
    except (OSError, ValueError, UnicodeError) as exc:
        result = validate(None)
        result["reason"] = type(exc).__name__
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] != "BLOCK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
