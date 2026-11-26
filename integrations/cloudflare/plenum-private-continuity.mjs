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


const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const ROLES = new Set(["intelligence","research","engineering","commercial","verification"]);
const DIGEST = /^[0-9a-f]{64}$/;
function checkpointValid(body) {
  return body && typeof body === "object" && !Array.isArray(body)
    && Object.keys(body).sort().join(",")==="attempt,expected_revision,issue,sha256,state"
    && UUID.test(body.issue) && Number.isInteger(body.attempt) && body.attempt>=1 && body.attempt<=2
    && Number.isInteger(body.expected_revision) && body.expected_revision>=0 && body.expected_revision<=4
    && ((body.state==="reserved" && body.sha256===null) ||
        (body.state==="completed" && typeof body.sha256==="string" && DIGEST.test(body.sha256)));
}
function checkpointTransition(current, body) {
  if (!current) return body.state==="reserved" && body.attempt===1;
  if (current.issue!==body.issue || current.state==="completed") return false;
  return (body.state==="completed" && body.attempt===current.attempt) ||
    (body.state==="reserved" && current.attempt===1 && body.attempt===2);
}

// This is a new namespace on the ALREADY DEPLOYED Cloudflare Worker, not a
// new resident server. The original public replay-guard namespace is untouched.
export class PrivateContinuityMemory {
  constructor(ctx) { this.ctx=ctx; }
  async fetch(request) {
    const url = new URL(request.url);
    const checkpointRole = url.pathname.match(/^\/checkpoint\/([a-z]+)$/)?.[1];
    if (checkpointRole && ROLES.has(checkpointRole)) {
      const key="checkpoint:"+checkpointRole;
      if (request.method==="GET") {
        const row=await this.ctx.storage.get(key);
        return row ? json(200,row) : json(404,{error:"not_found"});
      }
      if (request.method!=="POST") return json(405,{error:"method_not_allowed"});
      let body;
      try {body=await request.json();} catch {return json(400,{error:"invalid_checkpoint"});}
      if(!checkpointValid(body))return json(400,{error:"invalid_checkpoint"});
      return this.ctx.storage.transaction(async tx=>{
        const current=await tx.get(key);
        const revision=current?.revision||0;
        if(body.expected_revision!==revision)return json(409,{error:"stale_revision",current_revision:revision});
        if(!checkpointTransition(current,body))return json(409,{error:"invalid_transition"});
        const next={issue:body.issue,attempt:body.attempt,state:body.state,sha256:body.sha256,revision:revision+1};
        await tx.put(key,next);
        return json(200,next);
      });
    }
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

/* Separate runtime-only capability: no owner memory key, arbitrary text, private
 * records, list, dispatch, inference, or cross-mission access. Same DO binding,
 * separate instance; the runtime must be provisioned outside public CI. */
export async function handlePaperclipCheckpoint(request,env) {
  const url=new URL(request.url);
  const parts=url.pathname.split("/");
  const [,prefix,company,mission,role]=parts;
  if(parts.length!==5 || prefix!=="paperclip-checkpoints" || !UUID.test(company||"")
     || !UUID.test(mission||"") || !ROLES.has(role) || url.search
     || !["GET","POST"].includes(request.method))return json(404,{error:"route_not_found"});
  const secret=env?.PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET;
  if(!env?.PLENUM_PRIVATE_MEMORY || typeof secret!=="string" || secret.length<32
     || secret===env.PLENUM_PRIVATE_MEMORY_HMAC_SECRET
     || secret===env.PLENUM_WEBHOOK_HMAC_SECRET
     || env.PLENUM_PAPERCLIP_CHECKPOINT_SCOPE!==company+"/"+mission)
    return json(403,{error:"checkpoint_scope_unavailable"});
  if(Number(request.headers.get("content-length")||"0")>1024)return json(413,{error:"record_too_large"});
  // Stream with a hard byte cap even for chunked requests.
  let raw="";
  if(request.body){
    const reader=request.body.getReader();
    const chunks=[]; let size=0;
    try {
      while(true){
        const {done,value}=await reader.read();
        if(done)break;
        size+=value.byteLength;
        if(size>1024){void reader.cancel().catch(()=>{});return json(413,{error:"record_too_large"});}
        chunks.push(value);
      }
      const bytes=new Uint8Array(size);let offset=0;
      for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
      raw=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
    }catch{return json(400,{error:"invalid_checkpoint"});}
    finally{reader.releaseLock();}
  }
  if(!await verifyPrivateRequest(request,secret,raw))return json(403,{error:"unauthorized_or_stale"});
  if(request.method==="GET" && raw!=="")return json(400,{error:"invalid_checkpoint"});
  if(request.method==="POST"){
    let body;
    try{body=JSON.parse(raw);}catch{return json(400,{error:"invalid_checkpoint"});}
    if(!checkpointValid(body))return json(400,{error:"invalid_checkpoint"});
  }
  try{
    const object=env.PLENUM_PRIVATE_MEMORY.getByName("plenum-paperclip:"+company+":"+mission);
    return await object.fetch("https://continuity.internal/checkpoint/"+role,
       {method:request.method,...(request.method==="POST"?{headers:{"Content-Type":"application/json"},body:raw}:{})});
  }catch{return json(503,{error:"checkpoint_storage_unavailable"});}
}
