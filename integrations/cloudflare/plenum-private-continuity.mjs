/*
 * Explicit, owner-controlled continuity records on the EXISTING Plenum
 * Cloudflare Workers Free deployment, using a SEPARATE SQLite Durable Object.
 *
 * No import of user chats, Google Drive, financial/customer data or credentials.
 * Signed access requires a different owner-only secret from the public wake.
 * This is NOT a ChatGPT Memory hook or an MCP interface.
 */
const encoder = new TextEncoder();
const KEY = /^[a-z0-9][a-z0-9:_-]{0,79}$/;
const MAX_BYTES = 2900;
const MAX_CLOCK_SKEW = 120000;
const LEVELS = new Set(["VERIFIED", "FOUNDER_REPORTED", "PENDING", "OPEN", "BLOCKED"]);

function json(status, data) {
  return new Response(JSON.stringify(data), {status, headers:{
    "Content-Type":"application/json", "Cache-Control":"no-store",
    "X-Content-Type-Options":"nosniff"
  }});
}

function valid(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const allowed = ["key","summary","source","observed_at","level","expected_revision"];
  if (Object.keys(value).some(k => !allowed.includes(k)) ||
      allowed.some(k => !(k in value))) return false;
  if (typeof value.key !== "string" || !KEY.test(value.key) ||
      typeof value.summary !== "string" || value.summary.length < 8 ||
      value.summary.length > 1250 ||
      typeof value.source !== "string" || value.source.length > 500 ||
      typeof value.observed_at !== "string" ||
      typeof value.level !== "string" || !LEVELS.has(value.level) ||
      !Number.isSafeInteger(value.expected_revision) ||
      value.expected_revision < 0) return false;
  try {
    const u = new URL(value.source);
    if (u.protocol !== "https:" || u.username || u.password) return false;
  } catch { return false; }
  const time = Date.parse(value.observed_at);
  return Number.isFinite(time) && /^\d{4}-\d\d-\d\dT/.test(value.observed_at);
}

export async function verifyPrivateRequest(request, secret, raw, now = Date.now()) {
  if (typeof secret !== "string" || secret.length < 32) return false;
  const timestamp = request.headers.get("x-plenum-memory-time") || "";
  const signed = request.headers.get("x-plenum-memory-signature") || "";
  if (!/^\d{13}$/.test(timestamp) || Math.abs(now - Number(timestamp)) > MAX_CLOCK_SKEW ||
      !/^sha256=[a-fA-F0-9]{64}$/.test(signed)) return false;
  const key = await crypto.subtle.importKey("raw",encoder.encode(secret),
      {name:"HMAC",hash:"SHA-256"},false,["verify"]);
  const bytes = Uint8Array.from(signed.slice(7).match(/.{2}/g), v => parseInt(v,16));
  const message = [request.method,new URL(request.url).pathname,timestamp,raw].join("\n");
  return crypto.subtle.verify("HMAC",key,bytes,encoder.encode(message));
}

// This is a new namespace on the ALREADY DEPLOYED Cloudflare Worker, not a
// new resident server. The original public replay-guard namespace is untouched.
export class PrivateContinuityMemory {
  constructor(ctx) { this.ctx=ctx; }
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/put") {
      let data;
      try { data=await request.json(); } catch { return json(400,{error:"invalid_record"}); }
      if (!valid(data)) return json(400,{error:"invalid_record"});
      return this.ctx.storage.transaction(async tx => {
        const current = await tx.get("current:"+data.key);
        const revision = current?.revision || 0;
        if (data.expected_revision !== revision)
          return json(409,{error:"stale_revision",current_revision:revision});
        const next={key:data.key,summary:data.summary,source:data.source,
          observed_at:data.observed_at,level:data.level,revision:revision+1,
          stored_at:new Date().toISOString()};
        await tx.put("history:"+data.key+":"+(revision+1),next);
        await tx.put("current:"+data.key,next);
        return json(200,{status:"STORED",key:next.key,revision:next.revision});
      });
    }
    if (request.method === "GET" && url.pathname.startsWith("/get/")) {
      const key=url.pathname.slice(5);
      if (!KEY.test(key)) return json(400,{error:"invalid_key"});
      const current=await this.ctx.storage.get("current:"+key);
      return current ? json(200,current) : json(404,{error:"not_found"});
    }
    return json(404,{error:"route_not_found"});
  }
}

export async function handlePrivateMemory(request, env) {
  const url=new URL(request.url);
  const path=url.pathname;
  if (!((path==="/memory" && request.method==="POST") ||
        (path.startsWith("/memory/") && request.method==="GET")) ||
      url.search) return json(404,{error:"route_not_found"});
  if (!env?.PLENUM_PRIVATE_MEMORY || !env?.PLENUM_PRIVATE_MEMORY_HMAC_SECRET)
    return json(503,{error:"owner_private_memory_not_configured"});
  if (Number(request.headers.get("content-length")||"0")>MAX_BYTES)
    return json(413,{error:"record_too_large"});
  const raw=await request.text();
  if (encoder.encode(raw).length>MAX_BYTES)
    return json(413,{error:"record_too_large"});
  if (!await verifyPrivateRequest(request,env.PLENUM_PRIVATE_MEMORY_HMAC_SECRET,raw))
    return json(403,{error:"unauthorized_or_stale"});
  let internalPath;
  if (path==="/memory") {
    let body;
    try {body=JSON.parse(raw)}catch{return json(400,{error:"invalid_record"})}
    if (!valid(body))return json(400,{error:"invalid_record"});
    internalPath="/put";
  } else {
    const name=path.slice("/memory/".length);
    if(!KEY.test(name))return json(400,{error:"invalid_key"});
    internalPath="/get/"+name;
  }
  try {
    const object=env.PLENUM_PRIVATE_MEMORY.getByName("plenum-private-continuity");
    return await object.fetch("https://continuity.internal"+internalPath,{
      method:request.method,
      ...(request.method==="POST" ? {headers:{"Content-Type":"application/json"},body:raw}: {})
    });
  }catch {
    return json(503,{error:"private_storage_unavailable"});
  }
}
