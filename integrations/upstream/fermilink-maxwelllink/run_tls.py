"""Optional isolated run of the exact reviewed FermiLink/MaxwellLink TLS example.

No upstream code or distribution is bundled, no model/provider is called, and
nothing is downloaded. Supply the pinned upstream assets separately.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
FERMI_COMMIT = "1677243532ca1631750d5a62db9763c68291fddb"
MAXWELL_COMMIT = "122d655b0a6c61209ca23ae28efc3621e5283c85"
WHEEL = "maxwelllink-0.5.0-py3-none-any.whl"
INPUTS = {
    "em.py": (3601, "f4995083372ad7648769d6828c1f4b2aea8a645345cd2a828e7d676f91eabecb"),
    "config.json": (459, "6c920bc0576328b67d11001fd3488f8c7a787618a9dab174e9e01361f37b08ff"),
    WHEEL: (5146388, "512024415e0d075604803186579f7968ea3fc5ec2b0b56a14a005f020bdec886"),
}
BOOTSTRAP = """
import os, runpy, sys
def reject_external(event, args):
    if event.startswith("socket.") or event in {
        "subprocess.Popen", "os.system", "os.exec", "os.spawn",
        "os.posix_spawn", "os.fork", "os.forkpty",
    }:
        raise PermissionError("Python network/process operations are blocked")
sys.addaudithook(reject_external)
sys.path.insert(0, os.path.join(os.getcwd(), "maxwelllink-0.5.0-py3-none-any.whl"))
runpy.run_path("em.py", run_name="__main__")
"""


def validated_inputs(directory):
    if os.name != "posix":
        raise RuntimeError("Reviewed external process requires POSIX")
    if directory.is_symlink():
        raise ValueError("Input symlink directory refused")
    data = {}
    for name, (size, digest) in INPUTS.items():
        path = directory / name
        if path.is_symlink():
            raise ValueError("Input symlink refused")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size != size:
                raise ValueError(f"SHA-256/size mismatch for {name}")
            payload = file.read(size + 1)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"SHA-256 mismatch for {name}")
        data[name] = payload
    return data


def validate_history(payload):
    if len(payload) > 1_000_000:
        raise ValueError("Unexpected output size")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    expected = {"idx", "time_au", "Pe", "Pg", "Pge_real", "Pge_imag",
                "energy_au", "mux_au", "muy_au", "muz_au"}
    if len(rows) != 1000 or set(rows[0]) != expected:
        raise ValueError("Unexpected TLS output schema")
    numeric = [{k: float(v) for k, v in row.items()} for row in rows]
    if not all(math.isfinite(value) for row in numeric for value in row.values()):
        raise ValueError("Non-finite TLS result")
    pe = [row["Pe"] for row in numeric]
    pg = [row["Pg"] for row in numeric]
    times = [row["time_au"] for row in numeric]
    conservation = max(abs(a + b - 1) for a, b in zip(pe, pg))
    determinant = min(a*b - row["Pge_real"]**2 - row["Pge_imag"]**2
                      for a, b, row in zip(pe, pg, numeric))
    timestep_error = max(abs(t - (i+1)*0.5) for i, t in enumerate(times))
    if (
        conservation > 1e-8 or determinant < -1e-8 or timestep_error > 1e-8
        or min(pe+pg) < -1e-8 or max(pe+pg) > 1+1e-8
        or any(row["idx"] != i for i, row in enumerate(numeric))
    ):
        raise ValueError("TLS physical invariants failed")
    return {
        "sha256": hashlib.sha256(payload).hexdigest(), "rows": len(rows),
        "all_finite": True, "time_start_au": times[0], "time_end_au": times[-1],
        "max_population_conservation_error": conservation,
        "min_density_matrix_determinant": determinant,
        "max_timestep_error_au": timestep_error,
        "Pe_min": min(pe), "Pe_max": max(pe),
        "max_abs_muz": max(abs(row["muz_au"]) for row in numeric),
    }


def execute(input_dir):
    data = validated_inputs(input_dir)
    reports = ROOT / "reports"
    out = reports / "fermilink-maxwelllink-tls"
    if out.exists() or out.is_symlink() or reports.is_symlink():
        raise FileExistsError("Refusing to overwrite or follow redirected report paths")
    with tempfile.TemporaryDirectory(prefix="plenum-tls-") as temp:
        work = Path(temp)
        for name, payload in data.items():
            (work / name).write_bytes(payload)
        proc = subprocess.Popen(
            [sys.executable, "-I", "-c", BOOTSTRAP], cwd=work,
            env={"PATH": os.defpath, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            stdout, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise
        if proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode, proc.args, output=stdout)
        result = validate_history((work / "tls_history.csv").read_bytes())
    out.mkdir(parents=True, exist_ok=False)
    # Save only measured summary and hash, not copyleft inputs or raw CSV.
    receipt = {
        "fermilink_commit": FERMI_COMMIT,
        "maxwelllink_commit": MAXWELL_COMMIT,
        "input_sha256": {key: digest for key, (_, digest) in INPUTS.items()},
        "output": result, "model_inference": False, "paid_model_api_calls": 0,
        "redistributed_upstream_code": False,
        "scientific_discovery": False, "AGI_demonstrated": False,
        "limitation": "Original xy drive is orthogonal to z-oriented TLS; baseline evolution, not demonstrated laser-induced population transfer.",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(f"Validated baseline TLS receipt: {out.relative_to(ROOT) / 'receipt.json'}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, help="Directory holding exact pinned upstream assets")
    parser.add_argument("--execute", action="store_true", help="Explicitly authorize reviewed local template")
    args = parser.parse_args(argv)
    if args.execute:
        if args.inputs_dir is None:
            parser.error("--execute requires --inputs-dir")
        execute(args.inputs_dir)
    else:
        print(json.dumps({
            "mode": "read-only plan; no download or execution",
            "fermilink_commit": FERMI_COMMIT, "maxwelllink_commit": MAXWELL_COMMIT,
            "required_inputs": list(INPUTS), "model_inference": False,
            "paid_model_api_calls": 0,
        }, indent=2))


if __name__ == "__main__":
    main()
