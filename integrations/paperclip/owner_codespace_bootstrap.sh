#!/usr/bin/env bash
# Manual owner task in the exact temporary Codespace only. Never public CI.
set -euo pipefail
set +x
umask 077
stage=authorization
board_started=0
model_started=0
cleanup(){
  status=$?
  if [ "$model_started" = 1 ]; then docker stop --time 30 plenum-paperclip-qwen >/dev/null 2>&1 || true; fi
  if [ "$board_started" = 1 ]; then docker stop --time 60 plenum-paperclip-production >/dev/null 2>&1 || true; fi
  printf 'OWNER_TASK_STAGE=%s EXIT=%s\n' "$stage" "$status"
}
trap cleanup EXIT
test "${GITHUB_ACTIONS:-}" != true
test "${CODESPACES:-}" = true
test "${CODESPACE_NAME:-}" = silver-potato-pj4qv74gx9grh94gp
test "${1:-}" = --confirm-owner-free-budget
base=5741225d746a0f456f9166baf2ce815a08b99fd6
cd "$(git rev-parse --show-toplevel)"
test "$(git rev-parse HEAD^)" = "$base"
test "$(git diff --name-only "$base" HEAD | sort)" = "$(printf '%s\n' .vscode/tasks.json integrations/paperclip/owner_codespace_bootstrap.sh | sort)"
git diff --quiet HEAD --
stage=readiness
command -v docker
docker info --format 'Docker server {{.ServerVersion}}'
printf 'Available RAM and disk:\n'; free -m; df -h .
# Reject existing resources; no overwrites or ambiguous rerun.
for c in plenum-paperclip-production plenum-paperclip-qwen; do
  if docker container inspect "$c" --format '{{.Id}}' >/dev/null 2>&1; then echo "Existing container: $c; owner inspection required"; exit 1; fi
done
for v in plenum-paperclip-production plenum-paperclip-qwen-cache; do
  if docker volume inspect "$v" --format '{{.Name}}' >/dev/null 2>&1; then echo "Existing volume: $v; owner inspection required"; exit 1; fi
done
owner="$HOME/.plenum-owner"; grant="$HOME/.plenum-checkpoint"
test ! -e "$owner" && test ! -L "$owner"
test ! -e "$grant" && test ! -L "$grant"
stage=pinned_image
image=ghcr.io/paperclipai/paperclip:2026.1106.0
docker pull "$image" >/dev/null
test "$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = d69631b01b9c658f80bf8bed389863dce82643e1
node_uid="$(docker run --rm --network none --user node --entrypoint id "$image" -u)"
test "$node_uid" = "$(id -u)"
stage=private_local_files
mkdir -m 700 "$owner" "$grant"
python3 - "$owner/board.env" <<'PY'
import os,secrets,sys
fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,"w") as f:
    for key in ("BETTER_AUTH_SECRET","PAPERCLIP_TOOL_ACTION_SIGNING_SECRET"):
        f.write(key+"="+secrets.token_hex(32)+"\n")
PY
test "$(stat -c '%a:%u' "$owner/board.env")" = "600:$(id -u)"
test "$(stat -c '%a:%u' "$grant")" = "700:$node_uid"
stage=board
docker volume create plenum-paperclip-production >/dev/null
set -a
. "$owner/board.env"
set +a
docker run -d --name plenum-paperclip-production --restart no \
 -e HOST=127.0.0.1 -e PAPERCLIP_BIND=loopback -e PAPERCLIP_HOME=/paperclip \
 -e PAPERCLIP_DEPLOYMENT_MODE=local_trusted -e PAPERCLIP_DEPLOYMENT_EXPOSURE=private \
 -e PAPERCLIP_PUBLIC_URL=http://localhost:3100 -e BETTER_AUTH_SECRET -e PAPERCLIP_TOOL_ACTION_SIGNING_SECRET \
 --mount "type=volume,src=plenum-paperclip-production,dst=/paperclip" \
 --mount "type=bind,src=$PWD,dst=/plenum,readonly" \
 --mount "type=bind,src=$grant,dst=/run/plenum-checkpoint,readonly" "$image" >/dev/null
board_started=1
unset BETTER_AUTH_SECRET PAPERCLIP_TOOL_ACTION_SIGNING_SECRET
test -z "$(docker port plenum-paperclip-production)"
test "$(docker inspect plenum-paperclip-production --format '{{.HostConfig.NetworkMode}}')" != host
ready=false
for i in $(seq 1 90); do
 if docker exec plenum-paperclip-production curl --fail --silent http://127.0.0.1:3100/api/health >/dev/null; then ready=true;break;fi
 sleep 2
done
test "$ready" = true
docker exec --user node -e PYTHONPATH=/plenum/src plenum-paperclip-production python3 -c 'import sys;sys.path.insert(0,"/plenum/integrations/paperclip");from acceptance import api; assert api("/api/companies")==[]; print("Private empty native board healthy")'
stage=local_model
docker pull ollama/ollama:latest >/dev/null
docker run -d --name plenum-paperclip-qwen --restart no --network container:plenum-paperclip-production \
 -e OLLAMA_HOST=127.0.0.1:11434 -e OLLAMA_CONTEXT_LENGTH=2048 -e OLLAMA_NUM_PARALLEL=1 \
 --memory=5g --cpus=2 --mount type=volume,src=plenum-paperclip-qwen-cache,dst=/root/.ollama ollama/ollama:latest >/dev/null
model_started=1
ready=false
for i in $(seq 1 45); do
 if docker exec plenum-paperclip-production curl --fail --silent http://127.0.0.1:11434/api/tags >/dev/null; then ready=true;break;fi
 sleep 2
done
test "$ready" = true
bash integrations/paperclip/pull_original_qwen.sh >"$owner/model-pull.log" 2>&1
test "$(docker exec plenum-paperclip-qwen ollama list | awk '$1=="qwen3.5:4b" {print $2}')" = d8b0f5e9760c
stage=preflight
docker exec --user node -e PYTHONPATH=/plenum/src -e PLENUM_PERSISTENT_BOARD=confirmed -e PLENUM_PAPERCLIP_MODEL=local plenum-paperclip-production python3 /plenum/integrations/paperclip/sequential_mission.py preflight-live | tee "$owner/preflight.json"
stage=prepare
company="$(docker exec --user node -e PYTHONPATH=/plenum/src plenum-paperclip-production python3 -c 'import sys;sys.path.insert(0,"/plenum/integrations/paperclip");from acceptance import api;from lifecycle import canonical;assert api("/api/companies")==[];print(canonical(api("/api/companies","POST",{"name":"Plenum Prometheus private qualification","description":"Bounded private native workforce qualification"})["id"]))')"
printf '%s\n' "$company" >"$owner/company.uuid"
docker exec --user node -e PYTHONPATH=/plenum/src -e PLENUM_PERSISTENT_BOARD=confirmed -e PLENUM_PAPERCLIP_MODEL=local -e PLENUM_PERSISTENT_CHECKPOINT_MODE=remote -e PLENUM_PAPERCLIP_COMPANY_UUID="$company" -e PLENUM_MISSION_SCOPE='{"kind":"coastal"}' plenum-paperclip-production python3 /plenum/integrations/paperclip/sequential_mission.py prepare >"$owner/prepared.json"
python3 - "$owner/prepared.json" "$company" <<'PY'
import json,sys,uuid
rows=[]
for line in open(sys.argv[1]):
    try:r=json.loads(line)
    except ValueError:continue
    if isinstance(r,dict) and r.get("company")==sys.argv[2] and "mission" in r:rows.append(r)
assert len(rows)==1
r=rows[0]; assert str(uuid.UUID(r["mission"]))==r["mission"]
print(json.dumps({"company":r["company"],"mission":r["mission"],"prepared_only":True,"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0,"activation_performed":False}))
PY
stage=prepared_no_activation
