import {handlePrivateMemory, handlePaperclipCheckpoint, PrivateContinuityMemory} from "./plenum-private-continuity.mjs";
import {ownerMemoryCheckPage, ownerMemoryCheckScript} from "./plenum-private-memory-check.mjs";
import {handleFreeCodingAI} from "./plenum-free-coding-ai.mjs";
import {engineeringFallback, eligibleTick} from "./plenum-engineering-fallback.mjs";
export {PrivateContinuityMemory};
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
const REPLAY_LOCK_SECONDS = 300;

function response(status, data) {
  return new Response(JSON.stringify(data), {
    status, headers: {"Content-Type":"application/json", "Cache-Control":"no-store"}
  });
}

function freshStamp(stamp, nowSeconds = Math.floor(Date.now()/1000)) {
  return Number.isSafeInteger(stamp) && Math.abs(nowSeconds-stamp) <= MAX_AGE_SECONDS;
}

async function readBoundedBody(request, stamp) {
  if (!request.body || !freshStamp(stamp)) return null;
  const reader = request.body.getReader();
  const bytes = new Uint8Array(MAX_BYTES);
  let length = 0, timer, finished = false;
  // Time waiting for the body is wall time, not Worker CPU time.
  const deadline = (stamp + MAX_AGE_SECONDS + 1)*1000 - Date.now();
  const expired = new Promise(resolve => {
    timer = setTimeout(() => resolve(null), Math.max(0, deadline));
  });
  try {
    for (;;) {
      const part = await Promise.race([reader.read(), expired]);
      if (part === null || !freshStamp(stamp)) return null;
      if (part.done) {
        finished = true;
        return bytes.subarray(0, length);
      }
      if (part.value.byteLength > MAX_BYTES-length) return null;
      bytes.set(part.value, length);
      length += part.value.byteLength;
    }
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
    if (!finished) void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function authenticate(request, secret, nowSeconds = Math.floor(Date.now()/1000)) {
  if (typeof secret !== "string" || secret.length < 32) return null;
  const stamp = request.headers.get("x-plenum-timestamp") || "";
  const header = request.headers.get("x-plenum-signature") || "";
  if (!/^\d{10,12}$/.test(stamp) || !freshStamp(Number(stamp), nowSeconds)
      || !/^sha256=[0-9a-fA-F]{64}$/.test(header)) return null;
  const body = await readBoundedBody(request, Number(stamp));
  if (body === null) return null;
  const prefix = encoder.encode(stamp + ".");
  const message = new Uint8Array(prefix.length + body.length);
  message.set(prefix);
  message.set(body, prefix.length);
  const bytes = new Uint8Array(header.slice(7).match(/.{2}/g).map(v => parseInt(v, 16)));
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), {name:"HMAC", hash:"SHA-256"}, false, ["verify"]
  );
  const ok = await crypto.subtle.verify("HMAC", key, bytes, message);
  if (!ok || !freshStamp(Number(stamp))) return null;
  try { return new TextDecoder("utf-8", {fatal:true, ignoreBOM:true}).decode(body); }
  catch { return null; }
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

// Durable Object RPC. SQLite-backed on Workers Free. Transaction protects against
// parallel dispatch; intentionally claims the issue BEFORE GitHub network I/O.
// If GitHub fails, fail closed until the short lock expires, never retry a write.
export class PublicWakeReplayGuard {
  constructor(ctx) { this.ctx = ctx; }
  // The legacy Durable Object HTTP interface remains fully supported and
  // avoids requiring a Cloudflare-only runtime import in Node source tests.
  async fetch(request) {
    const path=new URL(request.url).pathname;
    if (request.method === "POST" && path === "/claim-engineering-tick") {
      try {
        const {slot} = await request.json();
        const admitted = await this.ctx.storage.transaction(async (tx) => {
          if (!eligibleTick(slot)) return false;
          const previous = await tx.get("engineering-last-slot");
          if (previous !== undefined && (!Number.isSafeInteger(previous) || previous >= slot))
            return false;
          await tx.put("engineering-last-slot", slot);
          return true;
        });
        return new Response(null,{status:admitted?204:409});
      } catch { return new Response(null,{status:503}); }
    }
    if (request.method === "POST" && path === "/claim-ai") {
      try {
        const {day,reserve,maximum}=await request.json();
        return new Response(null,{status:await this.claimAi(day,reserve,maximum)?204:429});
      } catch { return new Response(null,{status:503}); }
    }
    if (request.method !== "POST" || path !== "/claim")
      return new Response(null, {status:404});
    try {
      const {issue, stamp} = await request.json();
      return new Response(null, {status:await this.claim(issue, stamp)});
    } catch {
      return new Response(null, {status:503});
    }
  }
  async claim(issue, stamp) {
    if (!Number.isSafeInteger(issue) || issue < 1 || issue >= 1000000000
        || !Number.isSafeInteger(stamp)) return 403;
    return this.ctx.storage.transaction(async (tx) => {
      const key = "issue:" + issue;
      const expires = await tx.get(key);
      // Revalidate with the Durable Object's own clock at the atomic claim,
      // including on transaction retry or delayed delivery to this object.
      const now = Math.floor(Date.now()/1000);
      if (!freshStamp(stamp, now)) return 403;
      if (typeof expires === "number" && expires > now) return 409;
      await tx.put(key, now + REPLAY_LOCK_SECONDS);
      return 204;
    });
  }

  async claimAi(day, reserve, maximum) {
    if (typeof day !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(day)
        || !Number.isInteger(reserve) || reserve !== 200
        || !Number.isInteger(maximum) || maximum !== 4000
        || day !== new Date().toISOString().slice(0,10)) return false;
    return this.ctx.storage.transaction(async tx => {
      const key="free-original-ai:"+day;
      const used=await tx.get(key) || 0;
      if (!Number.isSafeInteger(used) || used+reserve>maximum) return false;
      await tx.put(key,used+reserve);
      return true;
    });
  }
}

export default {
  async scheduled(controller, env) {
    controller.noRetry();
    const status = await engineeringFallback(controller, env);
    console.log("Plenum bounded engineering fallback:", status);
  },
  async fetch(request, env) {
    const pathname = new URL(request.url).pathname;
    // Public branch previews must never reach owner memory, AI or dispatch,
    // even if the provider's Preview Base accidentally supplies bindings.
    if (env?.PLENUM_PREVIEW_ONLY === "true") {
      if (pathname === "/health" && request.method === "GET")
        return response(200, {state:"ISOLATED_PREVIEW_HEALTH_ONLY", no_model:true});
      return response(404, {error:"preview_route_disabled"});
    }
    if (pathname === "/ai/v1/chat/completions") return handleFreeCodingAI(request, env);
    if (pathname === "/memory-check" && request.method === "GET")
      return ownerMemoryCheckPage();
    if (pathname === "/memory-check.js" && request.method === "GET")
      return ownerMemoryCheckScript();
    if (pathname.startsWith("/paperclip-checkpoints/"))
      return handlePaperclipCheckpoint(request, env);
    if (pathname === "/memory" || pathname.startsWith("/memory/"))
      return handlePrivateMemory(request, env);
    if (pathname === "/health" && request.method === "GET")
      return response(200, {state:"REACHABLE_NOT_A_RUNNING_AGENT", no_model:true,
        source_contract_revision:"original-oidc-and-openhands-chat-v2",
        ai_binding_present:typeof env?.AI?.run === "function"});
    if (pathname !== "/wake" || request.method !== "POST")
      return response(404, {error:"route_not_found"});
    if (!env?.PLENUM_WEBHOOK_HMAC_SECRET || !env?.PLENUM_GITHUB_DISPATCH_TOKEN
        || !env?.PLENUM_REPLAY_GUARD)
      return response(503, {error:"owner_secrets_not_configured"});
    if (Number(request.headers.get("content-length") || "0") > MAX_BYTES)
      return response(413, {error:"payload_too_large"});
    const raw = await authenticate(request, env.PLENUM_WEBHOOK_HMAC_SECRET);
    if (raw === null) return response(403, {error:"unauthorized_or_stale"});
    const number = parsePublicIssueId(raw);
    if (number === null) return response(400, {error:"public_issue_id_required"});
    // A valid HMAC and fresh timestamp do not prevent replay. Claim once using
    // strongly consistent Durable Object storage before external dispatch.
    try {
      const guard = env.PLENUM_REPLAY_GUARD.getByName("plenum-public-wake");
      const replay = await guard.fetch("https://replay-guard.internal/claim", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({issue:number, stamp:Number(request.headers.get("x-plenum-timestamp"))})
      });
      if (replay.status === 403) return response(403, {error:"unauthorized_or_stale"});
      if (replay.status === 409) return response(409, {error:"duplicate_issue_wake"});
      if (replay.status !== 204) return response(503, {error:"replay_guard_unavailable"});
    } catch {
      return response(503, {error:"replay_guard_unavailable"});
    }
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

