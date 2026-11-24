"""Bounded checkpoint retry audit; no arbitrary fallback or replay of completed work."""
from pathlib import Path
from hashlib import sha256
from checkpoint_store import checked,encoded,exclusive

def recovery_receipt(directory,company,role,issue,result_digest):
    path=Path(directory);identity={"company":company,"role":role,"issue":issue}
    second=path/(role+".attempt-2")
    failure=path/(role+".failure-1")
    if not second.exists():
        if failure.exists():raise ValueError("Failure without accepted recovery")
        return None
    first=checked(path/(role+".attempt-1"),dict(identity,attempt=1))
    retry=checked(second,dict(identity,attempt=2))
    if failure.exists():
        f=checked(failure,dict(identity,attempt=1,retryable=True))
        reason="transient_failure"
        failure_hash=sha256(encoded(f)).hexdigest()
    else:
        reason="interrupted_reservation"
        failure_hash=None
    return {**identity,"reason":reason,"attempts":2,"failure_sha256":failure_hash,
            "first_reservation_sha256":sha256(encoded(first)).hexdigest(),"second_reservation_sha256":sha256(encoded(retry)).hexdigest(),
            "result_sha256":result_digest,"paid_inference":False}

def finalize(directory,company,role,issue,result_digest):
    row=recovery_receipt(directory,company,role,issue,result_digest)
    target=Path(directory)/(role+".recovery.json")
    if row is None:
        if target.exists():raise ValueError("Unexpected recovery receipt")
    elif target.exists():
        if checked(target,row)!=row:raise ValueError("Recovery receipt changed")
    else:exclusive(target,row)
    return row

def verify(directory,company,role,issue,result_digest):
    row=recovery_receipt(directory,company,role,issue,result_digest)
    target=Path(directory)/(role+".recovery.json")
    if row is not None:
        if checked(target,row)!=row:raise ValueError("Recovery receipt changed")
    elif target.exists():raise ValueError("Unexpected recovery receipt")
    return row
