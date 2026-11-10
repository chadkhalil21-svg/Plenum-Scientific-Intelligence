#!/usr/bin/env bash
# Owner-invoked: free-tier Codespaces DEMONSTRATION ONLY, not a 24/7 service.
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose must be available in this Codespace or a private Docker host."
  exit 2
fi
if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL is required to create a private n8n encryption key."
  exit 2
fi
KEYFILE="$ROOT/.env"
if [[ ! -f "$KEYFILE" ]]; then
  printf 'N8N_ENCRYPTION_KEY=%s\n' "$(openssl rand -hex 32)" > "$KEYFILE"
  chmod 600 "$KEYFILE"
fi
docker compose --env-file "$KEYFILE" -f "$ROOT/docker-compose.codespace.yml" up -d
echo "Downloading free Qwen3 0.6B model into a private local Ollama volume..."
docker compose --env-file "$KEYFILE" -f "$ROOT/docker-compose.codespace.yml" exec -T ollama ollama pull qwen3:0.6b
echo "DEVELOPMENT INSTANCE READY. Keep the GitHub Codespaces port 5678 PRIVATE."
echo "Open the private forwarded 5678 port; create your own n8n admin login."
echo "Import plenum-business-workforce.json via n8n UI and create Ollama credential:"
echo "  Base URL: http://ollama:11434  (no API key)."
echo "Choose qwen3:0.6b in the imported model node. Execute manually."
echo "This does not run continuously after the Codespace stops or exhausts free quota."
