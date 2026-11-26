// Existing Free Worker, existing GitHub dispatch grant; no new HTTP route,
// inference, private memory access, credentials, or unrestricted command.
const REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence";
const API = "https://api.github.com/repos/" + REPO;
export const CRON = "*/5 * * * *";
const REGISTERED = [[935,"prometheus-hyperframes-local-qualification"],
                    [936,"prometheus-accepted-upstream-evidence-registry"]];
export const SLOT_MS = 300_000;
const MAX_DYNAMIC = 12;
export function dynamicEntry(pr) {
  if (!pr || !Number.isSafeInteger(pr.number) || pr.number<=0 ||
      REGISTERED.some(([n])=>n===pr.number) || pr.state!=="open" || pr.draft!==false ||
      pr.user?.login!=="chadkhalil21-svg" || pr.head?.repo?.full_name!==REPO ||
      pr.base?.repo?.full_name!==REPO || pr.base?.ref!=="main" ||
      typeof pr.head?.ref!=="string" || !/^prometheus-[a-z0-9][a-z0-9-]{0,100}$/.test(pr.head.ref) ||
      typeof pr.body!=="string") return null;
  const lines=pr.body.split(/\r?\n/).filter(x=>x.includes("plenum-engineering-observe-v1:"));
  if(lines.length!==1)return null;
  const m=/^<!-- plenum-engineering-observe-v1:([a-f0-9]{40}):([A-Za-z0-9 ._|-]{1,100}):([A-Za-z0-9 ._|-]{1,100}) -->$/.exec(lines[0]);
  if(!m || m[1]!==pr.head.sha)return null;
  return {number:pr.number,head:m[1]};
}

export function eligibleTick(scheduledTime, now = Date.now()) {
  return Number.isSafeInteger(scheduledTime) && scheduledTime > 0 &&
    scheduledTime % SLOT_MS === 0 && now >= scheduledTime &&
    now - scheduledTime < SLOT_MS;
}
// The provider's native scheduled timestamp can carry seconds/milliseconds.
// Canonicalize only the first minute of the exact configured five-minute slot.
// Keep the original canonical-slot deadline, reject future timestamps, and
// never derive the reservation from arrival time (which could replay old ticks).
export function resolveScheduledTick(controller, now=Date.now()) {
  if (controller?.cron !== CRON) return {slot:null,reason:"CRON_MISMATCH"};
  const raw=controller.scheduledTime;
  if (!Number.isSafeInteger(raw) || raw<=0 || !Number.isSafeInteger(now))
    return {slot:null,reason:"INVALID_TIMESTAMP"};
  if (raw>now) return {slot:null,reason:"FUTURE_TIMESTAMP"};
  const slot=Math.floor(raw/SLOT_MS)*SLOT_MS;
  if (raw-slot>=60_000) return {slot:null,reason:"OUTSIDE_SCHEDULED_MINUTE"};
  if (!eligibleTick(slot,now)) return {slot:null,reason:"STALE_CANONICAL_SLOT"};
  return {slot,reason:raw===slot?"EXACT_SLOT":"NORMALIZED_SCHEDULED_MINUTE"};
}
function isRegisteredOpen(pr, number, branch) {
  return pr?.number === number && pr.state === "open" &&
    pr.user?.login === "chadkhalil21-svg" &&
    pr.head?.ref === branch && pr.head?.repo?.full_name === REPO &&
    pr.base?.ref === "main" && pr.base?.repo?.full_name === REPO &&
    /^[a-f0-9]{40}$/.test(pr.head?.sha || "");
}

export async function engineeringFallback(controller, env, {fetcher=fetch, clock=Date.now}={}) {
  // Internal scheduled events only; preview is never allowed to dispatch.
  if (env?.PLENUM_PREVIEW_ONLY === "true" ||
      env?.PLENUM_ENGINEERING_FALLBACK_ENABLED !== "true")
    return "DISABLED";
  const {slot}=resolveScheduledTick(controller,clock());
  if (slot===null) return "INVALID_OR_STALE_TICK";
  if (!env.PLENUM_GITHUB_DISPATCH_TOKEN || !env.PLENUM_REPLAY_GUARD)
    return "MISSING_EXISTING_BINDINGS";
  // Workers does not implement redirect:"error". Manual never follows a
  // redirect, and the explicit status checks below reject all 3xx responses.
  const headers = {"Authorization":"Bearer "+env.PLENUM_GITHUB_DISPATCH_TOKEN,
    "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2026-03-10",
    "User-Agent":"PlenumEngineeringFallback/1"};
  try {
    // Two fixed public PRs only. When no approved work is open, do not
    // provision a GitHub runner. A failed provider read never dispatches.
    let open = false;
    for (const [number,branch] of REGISTERED) {
      const res = await fetcher(API+"/pulls/"+number,{headers,redirect:"manual",
        signal:AbortSignal.timeout(8000)});
      if (!res.ok) return "READ_UNAVAILABLE";
      const body = await res.json();
      if (isRegisteredOpen(body, number, branch)) open = true;
    }
    // Discover new, explicitly admitted exact-head PRs without another code change.
    // Do not use body text as instructions or allow any caller-supplied endpoint.
    if (!open) {
      const res=await fetcher(API+"/pulls?state=open&base=main&per_page=100",{headers,redirect:"manual",signal:AbortSignal.timeout(8000)});
      if(!res.ok)return "READ_UNAVAILABLE";
      const rows=await res.json();
      if(!Array.isArray(rows)||rows.length>=100)return "READ_UNAVAILABLE";
      const entries=rows.map(dynamicEntry).filter(Boolean);
      if(entries.length>MAX_DYNAMIC||new Set(entries.map(x=>x.number)).size!==entries.length)return "READ_UNAVAILABLE";
      open=entries.length>0;
    }
    if (!open) return "NO_APPROVED_BACKLOG";
    if (!eligibleTick(slot,clock())) return "INVALID_OR_STALE_TICK";
    const guard = env.PLENUM_REPLAY_GUARD.getByName("plenum-engineering-fallback");
    const claim = await guard.fetch("https://replay-guard.internal/claim-engineering-tick",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({slot})
    });
    if (claim.status !== 204) return "RESERVATION_REJECTED";
    if (!eligibleTick(slot,clock())) return "INVALID_OR_STALE_TICK";
    // No raw task text or supplied URL. Reserve before the external write;
    // a failed or ambiguous dispatch is never retried within the same slot.
    const result = await fetcher(API+"/dispatches",{
      method:"POST",headers:{...headers,"Content-Type":"application/json"},
      redirect:"manual",signal:AbortSignal.timeout(8000),
      body:JSON.stringify({event_type:"plenum_engineering_backlog_tick_v1",
        client_payload:{slot}})
    });
    return result.status === 204 ? "DISPATCH_ACCEPTED_NOT_COMPLETED" : "DISPATCH_UNAVAILABLE";
  } catch {
    return "PROVIDER_UNAVAILABLE";
  }
}

// A one-time operational qualification of the original deployed cron. No
// work is fabricated and no idle recurring runner is enabled. At most two
// receipts, across deployments, within the founder's current UTC window.
export const CADENCE_START = Date.UTC(2026,10,26,8);
export const CADENCE_END = Date.UTC(2026,10,27,5);
export function eligibleCadenceSlot(slot, now=Date.now()) {
  return eligibleTick(slot,now) && slot>=CADENCE_START && slot<CADENCE_END;
}
export async function engineeringCadenceProof(controller,env,status,{fetcher=fetch,clock=Date.now}={}) {
  const {slot}=resolveScheduledTick(controller,clock());
  if (env?.PLENUM_PREVIEW_ONLY === "true" ||
      env?.PLENUM_ENGINEERING_FALLBACK_ENABLED !== "true" ||
      controller?.cron!==CRON || status!=="NO_APPROVED_BACKLOG" ||
      !eligibleCadenceSlot(slot,clock()) || !env.PLENUM_REPLAY_GUARD ||
      !env.PLENUM_GITHUB_DISPATCH_TOKEN || typeof env.PLENUM_WEBHOOK_HMAC_SECRET!=="string" ||
      env.PLENUM_WEBHOOK_HMAC_SECRET.length<32) return "CADENCE_NOT_ELIGIBLE";
  try {
    const guard=env.PLENUM_REPLAY_GUARD.getByName("plenum-engineering-fallback");
    const claim=await guard.fetch("https://replay-guard.internal/claim-cadence-proof",{
      method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({slot})});
    if (claim.status!==204) return "CADENCE_NOT_RESERVED";
    if (!eligibleCadenceSlot(slot,clock())) return "CADENCE_STALE_RESERVED";
    // Domain-separated attestation; never log the signature or secret.
    const encoder=new TextEncoder();
    const key=await crypto.subtle.importKey("raw",encoder.encode(env.PLENUM_WEBHOOK_HMAC_SECRET),
      {name:"HMAC",hash:"SHA-256"},false,["sign"]);
    const signed=new Uint8Array(await crypto.subtle.sign("HMAC",key,
      encoder.encode("plenum-engineering-cadence-v1."+slot+".cron_observation_only")));
    const signature=Array.from(signed,v=>v.toString(16).padStart(2,"0")).join("");
    if (!eligibleCadenceSlot(slot,clock())) return "CADENCE_STALE_RESERVED";
    const response=await fetcher(API+"/dispatches",{
      method:"POST",redirect:"manual",signal:AbortSignal.timeout(8000),
      headers:{"Authorization":"Bearer "+env.PLENUM_GITHUB_DISPATCH_TOKEN,
        "Accept":"application/vnd.github+json","Content-Type":"application/json",
        "X-GitHub-Api-Version":"2026-03-10","User-Agent":"PlenumCadenceProof/1"},
      body:JSON.stringify({event_type:"plenum_engineering_cadence_proof_v1",
        client_payload:{slot,scope:"cron_observation_only",signature}})});
    return response.status===204?"CADENCE_RECEIPT_DISPATCHED":"CADENCE_DISPATCH_UNAVAILABLE";
  } catch {return "CADENCE_UNAVAILABLE";}
}
