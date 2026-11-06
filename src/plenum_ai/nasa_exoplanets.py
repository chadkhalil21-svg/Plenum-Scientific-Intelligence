"""NASA Exoplanet Archive + Astropy: catalog consistency experiment.

Recalculates Keplerian periods from published semi-major axes and host masses.
IMPORTANT: many catalog semi-major axes are themselves derived using Kepler's
law; this is NOT necessarily an independent physical test of Kepler's law.
"""
from hashlib import sha256
from math import isfinite, pi
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

API = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
SOURCE = "NASA Exoplanet Archive Planetary Systems (ps, default_flag=1)"
SQL = (
    "select top 80 pl_name,pl_orbper,pl_orbsmax,st_mass "
    "from ps where default_flag=1 "
    "and pl_orbper is not null and pl_orbsmax is not null "
    "and st_mass is not null and pl_orbper>0 "
    "and pl_orbsmax>0 and st_mass>0 order by pl_name"
)
MAX_RESPONSE_BYTES = 180000


def query_url():
    return API + "?" + urlencode({"query": SQL, "format": "json"})


def nasa_records(opener=urlopen):
    request = Request(query_url(), headers={
        "User-Agent": "PlenumScientificIntelligence/0.8 (NASA public science verification)",
        "Accept": "application/json",
    })
    with opener(request, timeout=25) as response:
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("NASA response exceeded the bounded payload size")
    parsed = json.loads(payload)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        keys = [c["name"] for c in parsed["metadata"]]
        return [dict(zip(keys, row)) for row in parsed["data"]]
    raise ValueError("Unexpected NASA TAP JSON schema")


def predicted_period_days(semimajor_axis_au, host_mass_solar):
    """Kepler's third law for planet mass negligible compared to the host star."""
    from astropy import constants as const
    from astropy import units as u
    a = float(semimajor_axis_au)
    mass = float(host_mass_solar)
    if not (isfinite(a) and isfinite(mass) and 0 < a < 300 and 0 < mass < 100):
        raise ValueError("Planet parameters outside bounded positive range")
    period = 2 * pi * ((a * u.au)**3 / (const.G * mass * const.M_sun))**0.5
    return float(period.to_value(u.day))


def assess_catalog(rows):
    """Check reported catalog values against a model; do not assert independent proof."""
    good = []
    rejected = 0
    seen = set()
    for row in rows[:80]:
        try:
            name = str(row["pl_name"]).strip()
            p = float(row["pl_orbper"])
            a = float(row["pl_orbsmax"])
            m = float(row["st_mass"])
            if not name or name in seen or not isfinite(p) or not 0 < p < 200000:
                raise ValueError("Missing/duplicate/invalid catalog value")
            predicted = predicted_period_days(a, m)
            ratio = predicted / p
            if not isfinite(ratio) or ratio <= 0:
                raise ValueError("Nonfinite predicted period")
        except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError):
            rejected += 1
            continue
        seen.add(name)
        good.append({
            "planet": name,
            "catalog_period_days": p,
            "predicted_period_days": predicted,
            "semimajor_axis_au": a,
            "host_mass_solar": m,
            "absolute_fractional_difference": abs(ratio - 1),
        })
    if len(good) < 10:
        raise ValueError("Fewer than ten usable NASA catalog planets; refuse a population claim")
    errors = [x["absolute_fractional_difference"] for x in good]
    median_error = median(errors)
    ordered_names = sorted(x["planet"] for x in good)
    digest = sha256("\n".join(ordered_names).encode("utf-8")).hexdigest()
    consistent = sum(err < 0.10 for err in errors)
    return {
        "experiment": "Keplerian catalog-parameter consistency check",
        "hypothesis": "The NASA-reported orbital periods are consistent with the Keplerian periods computed from reported stellar masses and semimajor axes.",
        "source": SOURCE,
        "query_url": query_url(),
        "observations_evaluated": len(good),
        "records_rejected": rejected,
        "sample_names_sha256": digest,
        "median_absolute_fractional_difference": float(median_error),
        "within_ten_percent": consistent,
        "fraction_within_ten_percent": consistent / len(good),
        "examples": sorted(good, key=lambda x: x["planet"])[:8],
        "catalog_consistency_threshold": 0.75,
        "catalog_consistency_condition_met": consistent / len(good) >= 0.75,
        "independent_empirical_validation": False,
        "new_scientific_discovery_verified": False,
        "experimental_result_verified": False,
        "limitations": [
            "NASA's published semimajor axis may itself be calculated from the orbital period and stellar mass; the inputs can be mathematically dependent.",
            "This compares catalog parameters for consistency only and cannot independently establish Kepler's law.",
            "Host-star mass and orbital solutions have uncertainty; planet mass, multiplicity and non-Keplerian effects are neglected.",
            "The catalog is updated; a live TAP query is not an immutable archival snapshot. Preserve the recorded sample and run revision.",
        ],
    }


def run_nasa_catalog_consistency(opener=urlopen):
    return assess_catalog(nasa_records(opener=opener))
