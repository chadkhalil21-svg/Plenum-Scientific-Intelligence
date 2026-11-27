#!/usr/bin/env bash
# Only pre-inference transport recovery; no alternate model or registry.
set -euo pipefail
log=$(mktemp)
trap 'rm -f "$log"' EXIT
for attempt in 1 2 3; do
    if timeout 300 docker exec plenum-paperclip-qwen ollama pull qwen3.5:4b >"$log" 2>&1; then
        cat "$log"
        exit 0
    else
        status=$?
        cat "$log" >&2
        if [ "$status" -ne 1 ] || [ "$attempt" -ge 3 ] || ! grep -Eq '^Error: (pull model manifest: )?503(:|[[:space:]]|$)' "$log"; then
            exit "$status"
        fi
        echo "Transient model download HTTP 503 before inference; retry $((attempt + 1))/3" >&2
        sleep "$((attempt * 5))"
    fi
done
exit 1
