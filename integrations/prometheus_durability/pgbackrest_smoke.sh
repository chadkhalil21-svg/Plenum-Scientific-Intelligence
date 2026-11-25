#!/usr/bin/env bash
# Actual PostgreSQL / pgBackRest, isolated temporary cluster and repository.
set -euo pipefail
test "$GITHUB_ACTIONS" = true
test "$GITHUB_RUN_ATTEMPT" = 1
test "$(id -u)" -ne 0
archive=$(realpath "$1")
output=$(realpath -m "$2")
here=$(cd "$(dirname "$0")" && pwd)
p=$(mktemp -d /tmp/plenum-pgbackrest.XXXXXXXX)
sudo chown postgres:postgres "$p"
sudo chmod 700 "$p"
bin=/usr/lib/postgresql/16/bin
cfg="$p/pgbackrest.conf"
port=55439
aspg(){ sudo -u postgres -- "$@"; }
pgbr(){ aspg pgbackrest --config="$cfg" --stanza=plenum "$@"; }
cleanup(){ aspg "$bin/pg_ctl" -D "$p/db" -m fast stop >/dev/null 2>&1 || true; sudo rm -rf -- "$p"; }
trap cleanup EXIT
aspg mkdir -m 700 "$p/repo" "$p/log" "$p/lock" "$p/spool" "$p/socket"
aspg "$bin/initdb" -D "$p/db" --auth-local=trust --auth-host=reject --no-locale >/dev/null
aspg tee "$cfg" >/dev/null <<EOF
[global]
repo1-path=$p/repo
repo1-retention-full=2
log-path=$p/log
lock-path=$p/lock
spool-path=$p/spool
process-max=2
[plenum]
pg1-path=$p/db
pg1-port=$port
pg1-socket-path=$p/socket
EOF
aspg tee -a "$p/db/postgresql.conf" >/dev/null <<EOF
listen_addresses = ''
port = $port
unix_socket_directories = '$p/socket'
archive_mode = on
archive_command = 'pgbackrest --config=$cfg --stanza=plenum archive-push %p'
EOF
aspg "$bin/pg_ctl" -D "$p/db" -l "$p/log/postgres.log" -w start >/dev/null
pgbr stanza-create
python "$here/postgres_fixture.py" sql "$archive" | aspg "$bin/psql" -h "$p/socket" -p "$port" -U postgres -d postgres -v ON_ERROR_STOP=1 -q
query='SELECT case_name,company,mission,qualification_sha256,scope_sha256,divisions,products FROM acceptance ORDER BY case_name'
aspg "$bin/psql" -h "$p/socket" -p "$port" -U postgres -d postgres -v ON_ERROR_STOP=1 -Atc "$query" > "$output.before"
python "$here/postgres_fixture.py" expected "$archive" > "$output.expected"
cmp "$output.before" "$output.expected"
pgbr check
pgbr --type=full --start-fast backup
pgbr verify
pgbr --output=json info > "$output.info.json"
aspg "$bin/pg_ctl" -D "$p/db" -m fast -w stop >/dev/null
# Original data directory no longer exists at the target. Restore a new one.
aspg mv "$p/db" "$p/old"
test ! -e "$p/db"
pgbr --type=immediate --target-action=promote restore
aspg "$bin/pg_ctl" -D "$p/db" -l "$p/log/restored.log" -w start >/dev/null
aspg "$bin/psql" -h "$p/socket" -p "$port" -U postgres -d postgres -v ON_ERROR_STOP=1 -Atc "$query" > "$output.after"
cmp "$output.expected" "$output.after"
pgbackrest version > "$output.version"
python - "$output" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1])
def read(ext):return Path(str(p)+ext).read_bytes()
def h(b):return hashlib.sha256(b).hexdigest()
rows=read(".after")
assert rows==read(".expected")==read(".before")
info=json.loads(read(".info.json"))
assert len(info)==1 and info[0]["status"]["code"]==0 and any(b["type"]=="full" and not b.get("error",False) for b in info[0]["backup"])
p.write_text(json.dumps({"schema":"plenum-pgbackrest-public-fixture-v1","pgbackrest_version":read(".version").decode().strip(),"rows":len(rows.splitlines()),"original_rows_sha256":h(rows),"restored_rows_sha256":h(rows),"repository_verification_passed":True,"new_data_directory":True,"actual_postgresql_restore":True,"native_paperclip_database_restored":False,"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0},sort_keys=True))
PY
