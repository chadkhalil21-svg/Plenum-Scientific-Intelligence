# Persistent owner runtime (candidate; qualify before deployment)
The same upstream Paperclip image and local trusted, loopback-only API remain the board. Use an existing owner-controlled Linux Docker host, no paid inference. Do not expose port 3100. Preserve the volume and back it up before upgrades. In this mode only deterministic bounded public missions are enabled; local model persistent mode is deliberately denied. The existing isolated CI model path remains unchanged.

```sh
docker pull ghcr.io/paperclipai/paperclip:2026.1106.0
docker volume create plenum-paperclip-production
# From an accepted checkout; use stable secrets held in a private password manager.
read -rs BETTER_AUTH_SECRET; export BETTER_AUTH_SECRET
read -rs PAPERCLIP_TOOL_ACTION_SIGNING_SECRET; export PAPERCLIP_TOOL_ACTION_SIGNING_SECRET
docker run -d --name plenum-paperclip-production --restart unless-stopped \
 -e HOST=127.0.0.1 -e PAPERCLIP_BIND=loopback -e PAPERCLIP_HOME=/paperclip \
 -e PAPERCLIP_DEPLOYMENT_MODE=local_trusted -e PAPERCLIP_DEPLOYMENT_EXPOSURE=private \
 -e PAPERCLIP_PUBLIC_URL=http://localhost:3100 -e BETTER_AUTH_SECRET -e PAPERCLIP_TOOL_ACTION_SIGNING_SECRET \
 --mount type=volume,src=plenum-paperclip-production,dst=/paperclip \
 --mount type=bind,src="$PWD",dst=/plenum,readonly ghcr.io/paperclipai/paperclip:2026.1106.0
unset BETTER_AUTH_SECRET PAPERCLIP_TOOL_ACTION_SIGNING_SECRET
```
Create or select an actual dedicated native company in the private board; never use CI UUIDs. The explicit PLENUM_PAPERCLIP_COMPANY_UUID must exist. On its first bounded mission, the qualifier provisions the exact six-agent roster; subsequent missions reuse it. Use only one operator submission at a time. Set PLENUM_PERSISTENT_BOARD=confirmed, PLENUM_PAPERCLIP_COMPANY_UUID, and approved PLENUM_MISSION_SCOPE in docker exec --user node -e PYTHONPATH=/plenum/src, then run /plenum/integrations/paperclip/sequential_mission.py qualify. Read the actual native parent UUID from the qualification result. Restart the same container and pass PLENUM_PAPERCLIP_MISSION_UUID to restart-readback with the same company and persistent mode. Evidence is keyed by company/parent; no claim of external hosting or unrestricted autonomy.

Cloudflare checkpoint credentials must be injected only into the owner runtime, never the native public CI. Exact per-mission scope must be provisioned before using remote checkpoints; multi-mission remote grant rotation is not automated. See runtime_checkpoint.py and the Cloudflare README. Profile work products are executed in six existing native processes, not eleven independent workers; Browser uses approved public API access, Creative is an unpublished storyboard, Marketing is an unlaunched experiment, Support is an unsent draft.

Persistent roster continuity uses the fixed reviewed `persistent_entrypoint.py` and exact visible command/role, with no stored environment bindings. The pinned upstream redacts all plaintext environment values, so no redacted value is accepted as proof. The company-level immutable roster receipt binds all six native IDs. A pre-fix candidate board with redacted legacy configuration or no original roster receipt is rejected; do not silently adopt or recreate it. Production migration of such a board requires an explicitly reviewed operator procedure.
