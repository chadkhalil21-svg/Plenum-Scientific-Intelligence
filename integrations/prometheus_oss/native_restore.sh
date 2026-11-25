#!/usr/bin/env bash
# Synthetic native DB disaster recovery only, same CI job, distinct volume and
# fresh network-isolated container. Raw database bytes never leave this runner.
set -euo pipefail
test "$GITHUB_ACTIONS" = true
test "$GITHUB_RUN_ATTEMPT" = 1
image=ghcr.io/paperclipai/paperclip:2026.1106.0
source=plenum-paperclip-integration
restored=plenum-paperclip-recovered
volume=plenum-paperclip-restored-volume
tmp=$(mktemp -d)
cleanup() {
  docker rm -fv "$restored" >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT
test "$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = d69631b01b9c658f80bf8bed389863dce82643e1
if docker inspect plenum-paperclip-qwen >/dev/null 2>&1; then exit 1; fi
test "$(docker inspect "$source" --format '{{.State.Running}}')" = true
docker cp "$source":/paperclip/plenum-mission-evidence/event-native-mission.json "$tmp/marker.json"
read -r company mission < <(python3 -c 'import json,sys,uuid; x=json.load(open(sys.argv[1])); print(str(uuid.UUID(x["company"])),str(uuid.UUID(x["mission"])))' "$tmp/marker.json")
docker cp "$source":/paperclip/plenum-mission-evidence/"$company"/"$mission"/qualification.json "$tmp/original.json"
docker stop --time 60 "$source" >/dev/null
test "$(docker inspect "$source" --format '{{.State.Running}}')" = false
# The source DB is cold. Backup is held outside both database volumes.
docker run --rm --network none --user root --entrypoint tar -v plenum-paperclip-test-volume:/source:ro "$image" -C /source -cf - . > "$tmp/native.tar"
test "$(stat -c %s "$tmp/native.tar")" -lt 1000000000
sha256sum "$tmp/native.tar" > "$tmp/native.sha256"
# Confirm actual Postgres storage in the cold volume (not only task JSON).
python3 - "$tmp/native.tar" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1]) as t:
    names=[m.name for m in t.getmembers() if m.isfile()]
    assert any(n.endswith("/PG_VERSION") for n in names)
    assert any(n.endswith("/global/pg_control") for n in names)
    assert any("/base/" in n for n in names)
PY
if docker volume inspect "$volume" >/dev/null 2>&1; then exit 1; fi
docker volume create "$volume" >/dev/null
sha256sum -c "$tmp/native.sha256" >/dev/null
docker run --rm -i --network none --user root --entrypoint tar -v "$volume":/restore "$image" -C /restore -xpf - < "$tmp/native.tar"
# Compare restored regular file bytes, including the actual database storage,
# before the restored server can mutate it.
docker run --rm --network none --user root --entrypoint tar -v "$volume":/restore:ro "$image" -C /restore -cf - . > "$tmp/restored.tar"
python3 - "$tmp/native.tar" "$tmp/restored.tar" "$tmp/backup-proof.json" <<'PY'
import sys,tarfile,hashlib,json,os
def manifest(path):
    out={}
    with tarfile.open(path) as t:
        for m in t.getmembers():
            if m.isfile():
                assert m.name not in out
                f=t.extractfile(m);h=hashlib.sha256()
                while b:=f.read(65536):h.update(b)
                out[m.name]=h.hexdigest()
    return out
a,b=manifest(sys.argv[1]),manifest(sys.argv[2]);assert a==b
h=hashlib.sha256()
with open(sys.argv[1],"rb") as f:
    while b:=f.read(65536):h.update(b)
json.dump({"backup_sha256":h.hexdigest(),"file_manifest_sha256":hashlib.sha256(json.dumps(a,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"restored_file_count":len(a),"postgres_file_count":sum("/base/" in k for k in a)},open(sys.argv[3],"w"),sort_keys=True)
PY
docker run -d --name "$restored" --network none \
  -e GITHUB_ACTIONS=true -e HOST=127.0.0.1 -e PAPERCLIP_BIND=loopback -e PAPERCLIP_HOME=/paperclip \
  -e PAPERCLIP_DEPLOYMENT_MODE=local_trusted -e PAPERCLIP_DEPLOYMENT_EXPOSURE=private \
  -e PAPERCLIP_PUBLIC_URL=http://localhost:3100 \
  -e BETTER_AUTH_SECRET="$(openssl rand -hex 32)" -e PAPERCLIP_TOOL_ACTION_SIGNING_SECRET="$(openssl rand -hex 32)" \
  --mount "type=volume,src=$volume,dst=/paperclip" --mount "type=bind,src=$GITHUB_WORKSPACE,dst=/plenum,readonly" "$image" >/dev/null
# Same pinned Python dependencies as original native execution; no model or provider.
docker cp "$RUNNER_TEMP/plenum-oss-deps" "$restored":/opt/plenum-oss-deps
for i in $(seq 1 120); do
  if docker exec "$restored" curl --fail --silent http://127.0.0.1:3100/api/health >/dev/null; then break; fi
  sleep 2
done
test "$(docker inspect "$restored" --format '{{.HostConfig.NetworkMode}}')" = none
docker exec --user node -e PYTHONPATH=/plenum/src "$restored" python3 /plenum/integrations/paperclip/event_native.py readback
docker cp "$restored":/paperclip/plenum-mission-evidence/"$company"/"$mission"/qualification.json "$tmp/recovered.json"
cmp "$tmp/original.json" "$tmp/recovered.json"
docker inspect "$source" --format '{{.Id}}' > "$tmp/source-id"
docker inspect "$restored" --format '{{.Id}}' > "$tmp/restored-id"
python3 - "$tmp" <<'PY'
import json,hashlib,sys,os
from pathlib import Path
p=Path(sys.argv[1]); q=json.loads((p/"recovered.json").read_text())
assert q["verified_divisions"]==5 and q["verified_profile_work_products"]==11 and q["paid_inference"] is False
a=(p/"source-id").read_bytes();b=(p/"restored-id").read_bytes();assert a!=b
row=json.loads((p/"backup-proof.json").read_text())
assert row["postgres_file_count"]>0
row.update(schema="plenum-native-cold-database-restore-v1",company=q["company"],mission=q["parent"],qualification_sha256=hashlib.sha256(json.dumps(q,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest(),
           source_container_sha256=hashlib.sha256(a).hexdigest(),restored_container_sha256=hashlib.sha256(b).hexdigest(),
           source_run_id=os.environ["GITHUB_RUN_ID"],source_commit=os.environ["GITHUB_SHA"],separate_volume=True,network_isolated=True,native_readback=True,raw_database_uploaded=False,
           verified_divisions=5,verified_profile_work_products=11,model_calls_replayed=0,provider_calls_replayed=0,paid_inference=False)
(p/"native-database-restore.json").write_text(json.dumps(row,sort_keys=True))
PY
docker cp "$tmp/native-database-restore.json" "$source":/paperclip/plenum-mission-evidence/native-database-restore.json
