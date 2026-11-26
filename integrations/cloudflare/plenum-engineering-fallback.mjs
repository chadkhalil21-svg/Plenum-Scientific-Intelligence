// Existing Free Worker, existing GitHub dispatch grant; no new HTTP route,
// inference, private memory access, credentials, or unrestricted command.
const REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence";
const API = "https://api.github.com/repos/" + REPO;
export const CRON = "*/5 * * * *";
const REGISTERED = [[935,"prometheus-hyperframes-local-qualification"],
                    [936,"prometheus-accepted-upstream-evidence-registry"]];
export const SLOT_MS = 300_000;

export function eligibleTick(scheduledTime, now = Date.now()) {
  return Number.isSafeInteger(scheduledTime) && scheduledTime > 0 &&
    scheduledTime % SLOT_MS === 0 && now >= scheduledTime &&
    now - scheduledTime < SLOT_MS;
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
  if (controller?.cron !== CRON || !eligibleTick(controller.scheduledTime, clock()))
    return "INVALID_OR_STALE_TICK";
  if (!env.PLENUM_GITHUB_DISPATCH_TOKEN || !env.PLENUM_REPLAY_GUARD)
    return "MISSING_EXISTING_BINDINGS";
  const headers = {"Authorization":"Bearer "+env.PLENUM_GITHUB_DISPATCH_TOKEN,
    "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2026-03-10",
    "User-Agent":"PlenumEngineeringFallback/1"};
  const slot = controller.scheduledTime;
  try {
    // Two fixed public PRs only. When no approved work is open, do not
    // provision a GitHub runner. A failed provider read never dispatches.
    let open = false;
    for (const [number,branch] of REGISTERED) {
      const res = await fetcher(API+"/pulls/"+number,{headers,redirect:"error",
        signal:AbortSignal.timeout(8000)});
      if (!res.ok) return "READ_UNAVAILABLE";
      const body = await res.json();
      if (isRegisteredOpen(body, number, branch)) open = true;
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
      redirect:"error",signal:AbortSignal.timeout(8000),
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
  const slot=controller?.scheduledTime;
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
      method:"POST",redirect:"error",signal:AbortSignal.timeout(8000),
      headers:{"Authorization":"Bearer "+env.PLENUM_GITHUB_DISPATCH_TOKEN,
        "Accept":"application/vnd.github+json","Content-Type":"application/json",
        "X-GitHub-Api-Version":"2026-03-10","User-Agent":"PlenumCadenceProof/1"},
      body:JSON.stringify({event_type:"plenum_engineering_cadence_proof_v1",
        client_payload:{slot,scope:"cron_observation_only",signature}})});
    return response.status===204?"CADENCE_RECEIPT_DISPATCHED":"CADENCE_DISPATCH_UNAVAILABLE";
  } catch {return "CADENCE_UNAVAILABLE";}
}
