"""Trusted standard-library API reference retrieval, not candidate execution."""
import ast
import hashlib
import inspect
import json
from pathlib import Path
import zipfile

def sha(raw): return hashlib.sha256(raw).hexdigest()

def reference(source):
    # Read source as data only. Resolve a fixed trusted allowlist, not arbitrary
    # imports or model-specified code. No remote requests or hidden test data.
    tree=ast.parse(source.decode("utf-8"))
    refs=[]
    if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
           and isinstance(n.func.value,ast.Name) and n.func.value.id=="json"
           and n.func.attr in ("load","loads","JSONDecoder") for n in ast.walk(tree)):
        for obj in (json.loads,json.JSONDecoder.__init__):
            refs.append({"api":obj.__qualname__,"signature":str(inspect.signature(obj)),
                         "documentation":inspect.getdoc(obj)})
    if not refs: raise ValueError("No trusted API reference matched")
    return refs

def bind_exhaustion(path):
    expected="1185c80e273bdb91e0268a4fb641b691f7f67a3c9048b39244cca3a38e22a411"
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=20992 or sha(path.read_bytes())!=expected:
        raise ValueError("Unbound exhausted execution")
    prefix="miniswe-1060-independent-correction/"
    with zipfile.ZipFile(path) as z:
        if len(z.namelist())!=19 or len(set(z.namelist()))!=19 or z.testzip() is not None or sum(i.file_size for i in z.infolist())>300000:
            raise ValueError("Invalid archived execution")
        def records(name): return [json.loads(x) for x in z.read(prefix+name).splitlines()]
        result=json.loads(z.read(prefix+"native-result.json"))
        actions=records("staged-actions.jsonl")
        grades=records("independent-feedback.jsonl")
        requests=records("model-reservations.jsonl")
        responses=records("model-responses.jsonl")
    keys={x["request_sha256"] for x in requests}
    if (result.get("exit_status")!="LimitsExceeded" or result.get("paid_inference") is not False
        or result.get("model_digest")!="d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
        or len(keys)!=12 or len(requests)!=12 or len(responses)!=12
        or {x["request_sha256"] for x in responses}!=keys or len(actions)!=12
        or actions[-1]["edits"]!=7 or len(grades)!=6
        or any(x["acceptance_passed"] is not False for x in grades)):
        raise ValueError("Original exhaustion evidence mismatch")
    return keys,expected
