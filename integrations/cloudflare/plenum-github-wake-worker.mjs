/*
 * Plenum no-new-charge *event-driven wake* (SOURCE TEMPLATE ONLY).
 * Cloudflare Worker holds no private task content or personal credentials.
 * Receives ONLY authenticated, replay-bounded existing PUBLIC issue IDs,
 * and calls GitHub repository_dispatch for the SAME original repository.
 * Does not run Paperclip, Hermes, Ollama, WhatsApp, or private tasks.
 */
const REPO_API = "https://api.github.com/repos/chadkhalil21-svg/Plenum-Scientific-Intelligence/dispatches";
const encoder = new TextEncoder();
const MAX_BYTES = 140;
const MAX_AGE_SECONDS = 120;

function response(status, data) {
  return new Response(JSON.stringify(data), {
    status, headers: {"Content-Type":"application/json", "Cache-Control":"no-store"}
  });
}

export async function authenticate(request, secret, nowSeconds = Math.floor(Date.now()/1000)) {
  if (typeof secret !== "string" || secret.length < 32) return null;
  const stamp = request.headers.get("x-plenum-timestamp") || "";
  const header = request.headers.get("x-plenum-signature") || "";
  if (!/^\d{10,12}$/.test(stamp) || Math.abs(nowSeconds - Number(stamp)) > MAX_AGE_SECONDS
      || !/^sha256=[0-9a-fA-F]{64}$/.test(header)) return null;
  const raw = await request.text();
  if (encoder.encode(raw).length > MAX_BYTES) return null;
  const bytes = new Uint8Array(header.slice(7).match(/.{2}/g).map(v => parseInt(v, 16)));
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), {name:"HMAC", hash:"SHA-256"}, false, ["verify"]
  );
  const ok = await crypto.subtle.verify("HMAC", key, bytes, encoder.encode(stamp + "." + raw));
  return ok ? raw : null;
}

export function parsePublicIssueId(raw) {
  let obj;
  try { obj = JSON.parse(raw); } catch { return null; }
  if (obj === null || Array.isArray(obj) || typeof obj !== "object"
      || Object.keys(obj).length !== 1
      || !Number.isSafeInteger(obj.issue_number)
      || obj.issue_number < 1 || obj.issue_number >= 1000000000) return null;
  return obj.issue_number;
}

export default {
  async fetch(request, env) {
    const pathname = new URL(request.url).pathname;
    if (pathname === "/health" && request.method === "GET")
      return response(200, {state:"REACHABLE_NOT_A_RUNNING_AGENT", no_model:true});
    if (pathname !== "/wake" || request.method !== "POST")
      return response(404, {error:"route_not_found"});
    if (!env?.PLENUM_WEBHOOK_HMAC_SECRET || !env?.PLENUM_GITHUB_DISPATCH_TOKEN)
      return response(503, {error:"owner_secrets_not_configured"});
    if (Number(request.headers.get("content-length") || "0") > MAX_BYTES)
      return response(413, {error:"payload_too_large"});
    const raw = await authenticate(request, env.PLENUM_WEBHOOK_HMAC_SECRET);
    if (raw === null) return response(403, {error:"unauthorized_or_stale"});
    const number = parsePublicIssueId(raw);
    if (number === null) return response(400, {error:"public_issue_id_required"});
    try {
      const result = await fetch(REPO_API, {
        method:"POST",
        headers:{
          "Authorization":"Bearer " + env.PLENUM_GITHUB_DISPATCH_TOKEN,
          "Accept":"application/vnd.github+json",
          "Content-Type":"application/json",
          "X-GitHub-Api-Version":"2026-03-10",
          "User-Agent":"PlenumPublicWake/1"
        },
        body:JSON.stringify({
          event_type:"plenum_public_issue_wakeup",
          client_payload:{issue_number:number}
        })
      });
      if (result.status !== 204) return response(502, {error:"dispatch_not_accepted"});
      return response(202, {status:"WAKE_REQUESTED_NOT_COMPLETED", public_issue:number});
    } catch {
      return response(503, {error:"dispatch_unavailable"});
    }
  }
};
