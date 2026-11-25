"""Read the exact previously accepted PUBLIC #912 artifact, not a new mission."""
import hashlib,json,re,zipfile
from pathlib import Path
from uuid import UUID
ARCHIVE_SHA="d57361b2e95ff4bf6e1270c784b3774fa555bfc478ca3b293adca40cb00f046d"
ORIGINAL_RUN="45569733612"
ORIGINAL_COMMIT="7d5e1f5a4020281d739827a22dab66a3fe396da1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def read_accepted(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1000000 or sha(path)!=ARCHIVE_SHA:raise ValueError("Original archive identity")
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=["fresh-runner-result.json"] or z.testzip() is not None or z.infolist()[0].file_size>100000:raise ValueError("Unsafe original ZIP")
        data=json.loads(z.read("fresh-runner-result.json"))
    if str(data["run_id"])!=ORIGINAL_RUN or data["commit"]!=ORIGINAL_COMMIT or data["fresh_runner_independent_acceptance"] is not True or data["paid_inference"] is not False or data["model_calls_replayed"]!=0 or data["provider_calls_replayed"]!=0:raise ValueError("Original qualification not accepted")
    cases=data["accepted"]
    if len(cases)!=9:raise ValueError("Nine original cases required")
    for name,row in cases.items():
        if not re.fullmatch(r"[a-z0-9-]{1,64}",name) or any(str(UUID(row[k]))!=row[k] for k in ("company","mission")) or any(not re.fullmatch("[0-9a-f]{64}",row[k]) for k in ("qualification_sha256","scope_sha256")):raise ValueError("Original mission identity")
        if row["verified_divisions"]!=5 or row["verified_profile_work_products"]!=11 or row["paid_inference"] is not False or row["model_calls_replayed"]!=0 or row["provider_calls_replayed"]!=0:raise ValueError("Original workforce acceptance")
    return cases
