"""Bounded AI-selected hypotheses tested later on genuinely withheld NOAA measurements.

All candidate models, sites, dates, score functions and acceptance rules
are fixed in reviewed source *before* testing. Qwen3 can independently choose
one of four models from development-only metrics; it cannot create code, call
arbitrary tools, alter dates, or see final-day measurements.

The first 12 days fit the development candidate, the following four days
score it, and the subsequent 24 hours stay sealed until the separate audit.
This is narrow automated model selection, NOT original physical discovery.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import math
import numpy as np

from .noaa_empirical import API, STATIONS, MAX_DOWNLOAD, parse_observations

CUTOFF_DATES = ("2026-01-17", "2026-04-17")
PERIODS = {
    "persistence_24h": (),
    "m2_only": (12.4206,),
    "m2_s2": (12.4206, 12.0),
    "four_constituents": (12.4206, 12.0, 23.9345, 25.8193),
}
LETTERS = "ABCD"
ORDER = tuple(PERIODS)
MAX_RESPONSE = MAX_DOWNLOAD
MIN_TRAIN, MIN_DEV, MIN_TEST = 250, 85, 20
EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def cutoff_date(value):
    if value not in CUTOFF_DATES:
        raise ValueError("Unapproved test day")
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def api_query(station, day, reveal_holdout=False):
    if station not in STATIONS:
        raise ValueError("Station not allowlisted")
    cutoff = cutoff_date(day)
    first = cutoff - timedelta(days=16)
    # Separate jobs: the proposer cannot even request the final day.
    last = cutoff if reveal_holdout else cutoff - timedelta(days=1)
    return API + "?" + urlencode({
        "begin_date": first.strftime("%Y%m%d"),
        "end_date": last.strftime("%Y%m%d"),
        "station": station, "product": "hourly_height",
        "datum": "MLLW", "time_zone": "gmt", "units": "metric",
        "format": "json", "application": "plenum_autonomous_science_v1",
    })


def fetch_observations(station, day, reveal_holdout=False, opener=urlopen):
    request = Request(api_query(station, day, reveal_holdout),
                      headers={"User-Agent": "PlenumScientificIntelligence/1.0 public observation research"})
    with opener(request, timeout=25) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("NOAA response exceeds bounded limit")
    response = json.loads(raw)
    if not isinstance(response, dict) or response.get("error") or not isinstance(response.get("data"), list):
        raise ValueError("No usable measured NOAA observations")
    return parse_observations(response["data"]), sha256(raw).hexdigest()


def _matrix(times, name):
    periods = PERIODS[name]
    if not periods:
        raise ValueError("Persistence has no fitted matrix")
    result = []
    for t in times:
        h = (t - EPOCH).total_seconds() / 3600
        row = [1.]
        for p in periods:
            row.extend((math.sin(math.tau*h/p), math.cos(math.tau*h/p)))
        result.append(row)
    return np.asarray(result, dtype=np.float64)


def _forecast(name, obs, fit_times, target_times):
    if name not in PERIODS:
        raise ValueError("Model outside allowlist")
    if not set(fit_times).isdisjoint(target_times):
        raise AssertionError("Target data used in fitting")
    if not target_times or any(t not in obs for t in target_times):
        raise ValueError("Missing measured target data")
    if name == "persistence_24h":
        prev = [t - timedelta(days=1) for t in target_times]
        if any(t not in obs for t in prev):
            raise ValueError("Missing baseline information")
        return [float(obs[t]) for t in prev]
    A = _matrix(fit_times, name)
    if len(A) < max(MIN_TRAIN, A.shape[1] * 12):
        raise ValueError("Insufficient measurements to fit")
    y = np.asarray([obs[t] for t in fit_times], dtype=float)
    weights, _r, rank, _s = np.linalg.lstsq(A, y, rcond=None)
    if rank < len(weights) or not np.all(np.isfinite(weights)):
        raise ValueError("Nonidentifiable harmonic fit")
    return list(map(float, _matrix(target_times, name) @ weights))


def _mae(obs, times, predictions):
    if len(predictions) != len(times):
        raise ValueError("Prediction length mismatch")
    return sum(abs(float(obs[t]) - p) for t, p in zip(times, predictions)) / len(times)


def _train_dev(obs, day):
    cutoff = cutoff_date(day)
    start = cutoff - timedelta(days=16)
    fit_cutoff = cutoff - timedelta(days=4)
    fit = sorted(t for t in obs if start <= t < fit_cutoff)
    dev = sorted(t for t in obs if fit_cutoff <= t < cutoff
                 and t - timedelta(days=1) in obs)
    if len(fit) < MIN_TRAIN or len(dev) < MIN_DEV:
        raise ValueError("Development-only NOAA coverage insufficient")
    if set(fit) & set(dev):
        raise AssertionError("Train/dev leakage")
    return fit, dev


def development_scores(obs, day):
    fit, dev = _train_dev(obs, day)
    scores = {}
    for name in ORDER:
        pred = _forecast(name, obs, fit, dev)
        scores[name] = _mae(obs, dev, pred)
    return {
        "train_hours": len(fit), "development_hours": len(dev),
        "scores_mae_m": scores, "holdout_measurements_seen": False,
        "fit_window": "first 12 days only", "development_window": "next four days",
    }


def selection_prompt(scores, station, day):
    """Only development metrics enter model context; final day is never included."""
    lines = [
        "You are an experimental scientific model selector.",
        "Choose exactly one of A B C D. No free code or external tools.",
        "The selection is a future, falsifiable prediction, NOT a discovery.",
        "The unseen test day is withheld; choose based on these development errors only.",
        f"Gauge: {STATIONS[station]}. Date to forecast (NO measurements supplied): {day}.",
        "Candidate model and development mean absolute error in meters:",
    ]
    for letter, name in zip(LETTERS, ORDER):
        lines.append(f"{letter}: {name} | {scores[name]:.6f} m")
    lines.extend([
        "Scientific aim: choose a reasonable forecast model, considering overfitting.",
        "Your choice will later be judged against 24h persistence and the fixed",
        "four-constituent reference on separately measured future-day observations.",
        "Choose one letter only: A, B, C, or D.",
    ])
    return "\n".join(lines)


def qwen_choose(prompt):
    from .hf_model import _load_model, APPROVED_MODEL
    tokenizer, model, torch = _load_model(APPROVED_MODEL)
    formatted = tokenizer.apply_chat_template([
        {"role": "user", "content": prompt}
    ], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    inputs = tokenizer(formatted, return_tensors="pt", truncation=True, max_length=768)
    ids = [tokenizer.encode(letter, add_special_tokens=False) for letter in LETTERS]
    if any(len(item) != 1 for item in ids):
        raise ValueError("Answer labels are not atomic tokens")
    with torch.inference_mode():
        logits = model(**inputs).logits[0, -1, :]
    scores = [float(logits[x[0]]) for x in ids]
    if any(not math.isfinite(score) for score in scores):
        raise ValueError("Invalid model choice scores")
    return LETTERS[max(range(len(scores)), key=lambda x: scores[x])]


def make_proposals(chooser, opener=urlopen):
    """Never downloads, reads, or scores the sealed test day."""
    if not callable(chooser):
        raise ValueError("A real model chooser or explicit test stub is required")
    items = []
    for day in CUTOFF_DATES:
        for station in STATIONS:
            obs, digest = fetch_observations(station, day, False, opener)
            metrics = development_scores(obs, day)
            prompt = selection_prompt(metrics["scores_mae_m"], station, day)
            selected_letter = chooser(prompt)
            if not isinstance(selected_letter, str) or selected_letter not in LETTERS:
                raise ValueError("AI gave invalid model selection; no fallback or fabrication")
            method = ORDER[LETTERS.index(selected_letter)]
            metrics["selected"] = method
            metrics["model_answer"] = selected_letter
            items.append({
                "station": station, "holdout_day": day,
                "development": metrics,
                "source_data_hash_sha256": digest,
                "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
                "hypothesis": (
                    f"{method} trained exclusively on the prior 16 days will beat "
                    "24h persistence on the still-unseen held-out date"
                ),
                "falsifier": "If selected model MAE is at least persistence MAE on the withheld 24 hours",
                "question_generator": "reviewed candidate templates; AI selects one of four",
                "selection_from_model": True,
            })
    return {
        "schema": "plenum-ai-hypothesis-proposals-v1",
        "precommitted_days": list(CUTOFF_DATES),
        "stations": list(STATIONS),
        "candidate_names": list(ORDER),
        "proposals": items,
        "Qwen_model": "Qwen/Qwen3-0.6B",
        "Qwen_revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "agent_accessed_test_measurements": False,
        "unrestricted_tool_execution": False,
        "production_model_changed": False,
        "hypotheses_new_physical_discoveries": False,
    }


def audit_proposals(proposals, opener=urlopen):
    """Separate audit receives frozen candidate names; no model inference."""
    if proposals.get("schema") != "plenum-ai-hypothesis-proposals-v1":
        raise ValueError("Unsupported research proposal manifest")
    cases = proposals.get("proposals", [])
    expected = [(day, s) for day in CUTOFF_DATES for s in STATIONS]
    if [(case.get("holdout_day"), case.get("station")) for case in cases] != expected:
        raise ValueError("Missing/reordered/unapproved station-date pairs")
    if proposals.get("candidate_names") != list(ORDER):
        raise ValueError("Candidate menu was altered")
    if proposals.get("agent_accessed_test_measurements") is not False:
        raise ValueError("Proposer was not blind")
    evaluations = []
    for case in cases:
        day, station = case["holdout_day"], case["station"]
        selected = case.get("development", {}).get("selected")
        if selected not in ORDER:
            raise ValueError("Unapproved model choice")
        if case["development"].get("model_answer") != LETTERS[ORDER.index(selected)]:
            raise ValueError("Choice and label disagree")
        obs, digest = fetch_observations(station, day, True, opener)
        cutoff = cutoff_date(day)
        train = sorted(t for t in obs if cutoff - timedelta(days=16) <= t < cutoff)
        test = sorted(t for t in obs if cutoff <= t < cutoff + timedelta(days=1)
                      and t - timedelta(days=1) in obs)
        if len(train) < 350 or len(test) < MIN_TEST or set(train) & set(test):
            raise ValueError("Insufficient independent final test observations")
        models = (selected, "persistence_24h", "four_constituents")
        error = {name: _mae(obs, test, _forecast(name, obs, train, test))
                 for name in set(models)}
        evaluations.append({
            "station": station, "holdout_day": day, "selected": selected,
            "test_hours": len(test), "training_hours": len(train),
            "observed_test_source_sha256": digest,
            "development_data_sha256": case["source_data_hash_sha256"],
            "chosen_model_mae_m": error[selected],
            "persistence_mae_m": error["persistence_24h"],
            "fixed_four_constituent_mae_m": error["four_constituents"],
            "chosen_beats_persistence": error[selected] < error["persistence_24h"],
            "chosen_beats_previous_four_term_reference": error[selected] < error["four_constituents"],
            "test_data_used_to_select_or_fit_hypothesis": False,
            "models_selected_after_test": False,
            "scientific_discovery": False,
        })
    return {
        "schema": "plenum-ai-hypothesis-audit-v1",
        "cases": evaluations,
        "trials": len(evaluations),
        "won_against_persistence": sum(x["chosen_beats_persistence"] for x in evaluations),
        "won_against_fixed_reference": sum(x["chosen_beats_previous_four_term_reference"] for x in evaluations),
        "agent_selected_from_fixed_hypothesis_menu": True,
        "agent_invented_new_equations": False,
        "AI_found_generalizable_improvement": False,
        "model_weights_updated": False,
        "eligible_for_automatic_deployment": False,
        "human_scientific_review_required": True,
        "limitations": [
            "This is constrained LLM hypothesis selection, not unrestricted autonomous invention.",
            "The 0.6B model sees development scores only; the external audit fetches final-day measurements afterward.",
            "Four station-day forecasts cannot establish robust generalization.",
            "No model changes or research results are promoted automatically.",
        ],
    }


def save_report(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(target)
