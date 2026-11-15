/*
 * Reuse the EXISTING Cloudflare Worker, AI binding, Github Actions OIDC, and
 * original pinned OpenHands SDK. No API keys, second host, code writes or browser.
 * Only original owner-founded PUBLIC issue repair job on main may call this.
 * No model-side tools, uploads, deployment, paid fallback or private data.
 */
const REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence";
const MODEL = "@cf/zai-org/glm-4.7-flash";
const AUDIENCE = "plenum-original-public-coder";
const ISSUER = "https://token.actions.githubusercontent.com";
const WORKFLOW = REPO + "/.github/workflows/business-workforce-runtime.yml@refs/heads/main";
const MAX_BYTES = 90000;
const DAILY_RESERVATION = 200;
const DAILY_LOCAL_MAX = 4000;
const encoder = new TextEncoder();

const fail = (status, error) => new Response(JSON.stringify({error:{message:error,type:"invalid_request_error"}}), {
  status, headers:{"Content-Type":"application/json","Cache-Control":"no-store"}
});
function decodePart(part) {
  if (typeof part !== "string" || !/^[A-Za-z0-9_-]+$/.test(part)) throw Error("invalid_jwt");
  const base = part.replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base.padEnd(Math.ceil(base.length / 4) * 4, "="));
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}
function parsePart(part) {
  return JSON.parse(new TextDecoder().decode(decodePart(part)));
}

export async function verifyOriginalGithubOIDC(token, {now = Math.floor(Date.now()/1000), fetcher = fetch, diagnostic = () => {}} = {}) {
  const reject = stage => { diagnostic(stage); return false; };
  if (typeof token !== "string" || token.length < 300 || token.length > 12000) return reject("shape");
  const parts = token.split(".");
  if (parts.length !== 3) return reject("parts");
  let header, claims;
  try { header = parsePart(parts[0]); claims = parsePart(parts[1]); } catch { return reject("decode"); }
  if (header.alg !== "RS256" || typeof header.kid !== "string"
      || header.kid.length > 200 || !/^[A-Za-z0-9_:-]+$/.test(header.kid)) return reject("header");
  if (claims.iss !== ISSUER || claims.aud !== AUDIENCE
      || claims.repository !== REPO
      || claims.sub !== "repo:" + REPO + ":ref:refs/heads/main"
      || claims.workflow_ref !== WORKFLOW
      || claims.event_name !== "issues"
      || !Number.isSafeInteger(claims.iat) || !Number.isSafeInteger(claims.exp)
      || claims.iat > now + 30 || claims.iat < now - 600
      || claims.exp <= now || claims.exp > now + 900) return reject("claims");
  try {
    const response = await fetcher(ISSUER + "/.well-known/jwks", {headers:{"Accept":"application/json"}});
    if (!response.ok) return reject("jwks_http");
    const jwks = await response.json();
    const key = Array.isArray(jwks.keys) && jwks.keys.find(k => k.kid === header.kid
        && k.kty === "RSA" && k.use === "sig" && k.alg === "RS256");
    if (!key) return reject("jwks_key");
    const imported = await crypto.subtle.importKey("jwk", key, {name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"}, false, ["verify"]);
    return await crypto.subtle.verify("RSASSA-PKCS1-v1_5", imported, decodePart(parts[2]),
                                      encoder.encode(parts[0]+"."+parts[1])) || reject("signature");
  } catch { return reject("jwks_or_crypto"); }
}

function asOpenAI(result, request) {
  const message = Array.isArray(result?.choices) ? result.choices[0]?.message : null;
  let content = message?.content ?? result?.response ?? result?.result ?? "";
  const nativeTools = message?.tool_calls ?? result?.tool_calls ?? [];
  if (typeof content !== "string") content = "";
  const tool_calls = Array.isArray(nativeTools) ? nativeTools.slice(0,8).map((t,i) => {
    const f = t?.function ?? t;
    if (!/^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(f?.name ?? "")) throw Error("unsupported_tool_response");
    return {id:String(t?.id ?? "call_"+i),type:"function",
      function:{name:f.name,arguments:typeof f.arguments==="string" ? f.arguments : JSON.stringify(f.arguments ?? {})}};
  }) : [];
  if (!content && !tool_calls.length) throw Error("empty_model_response");
  const created = Math.floor(Date.now()/1000);
  const id = "chatcmpl-plenum-"+created;
  const finish = tool_calls.length ? "tool_calls" : "stop";
  const usage = result?.usage ?? {};
  const base = {id,object:"chat.completion",created,model:request.model,
    choices:[{index:0,message:{role:"assistant",content:content || null,...(tool_calls.length?{tool_calls}:{})},finish_reason:finish}],
    usage:{prompt_tokens:Number.isSafeInteger(usage.prompt_tokens)?usage.prompt_tokens:0,
      completion_tokens:Number.isSafeInteger(usage.completion_tokens)?usage.completion_tokens:0,
      total_tokens:Number.isSafeInteger(usage.total_tokens)?usage.total_tokens:0}};
  return base;
}
export function encodeOpenAIResult(data, streaming=false) {
  if (!streaming) return new Response(JSON.stringify(data),{headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
  const message=data.choices[0].message;
  const chunk={id:data.id,object:"chat.completion.chunk",created:data.created,model:data.model,
    choices:[{index:0,delta:{role:"assistant",...(message.content?{content:message.content}:{}),
      ...(message.tool_calls?{tool_calls:message.tool_calls.map((t,index)=>({
          index,id:t.id,type:"function",function:t.function}))}:{})},finish_reason:null}]};
  const end={id:data.id,object:"chat.completion.chunk",created:data.created,model:data.model,
    choices:[{index:0,delta:{},finish_reason:data.choices[0].finish_reason}]};
  return new Response("data: "+JSON.stringify(chunk)+"\n\n"+"data: "+JSON.stringify(end)+"\n\n"+"data: [DONE]\n\n",{
    headers:{"Content-Type":"text/event-stream","Cache-Control":"no-store","X-Accel-Buffering":"no"}});
}

export async function handleFreeCodingAI(request, env, {verifier=verifyOriginalGithubOIDC}={}) {
  if (request.method !== "POST") return fail(405,"method_not_allowed");
  // There is NO paid inference route. This binding must be on Workers Free.
  if (env?.PLENUM_FREE_AI_ENABLED !== "true" || !env?.AI?.run || !env?.PLENUM_REPLAY_GUARD)
    return fail(503,"free_ai_binding_or_owner_gate_unavailable");
  const length=Number(request.headers.get("content-length") || "0");
  if (!Number.isFinite(length) || length > MAX_BYTES) return fail(413,"request_exceeds_free_budget_limit");
  const auth=request.headers.get("authorization") || "";
  const match=/^Bearer ([A-Za-z0-9._-]{300,12000})$/.exec(auth);
  if (!match) return fail(403,"unauthorized_original_workflow_format");
  let stage = "unspecified";
  if (!await verifier(match[1], {diagnostic: reason => { stage = reason; }}))
    return fail(403,"unauthorized_original_workflow_"+stage);
  let bodyText;
  try { bodyText=await request.text(); } catch { return fail(400,"unreadable_request"); }
  if (encoder.encode(bodyText).length > MAX_BYTES) return fail(413,"request_exceeds_free_budget_limit");
  let body;
  try { body=JSON.parse(bodyText); } catch { return fail(400,"invalid_json"); }
  if (!body || typeof body!=="object" || Array.isArray(body)
      || !["glm-4.7-flash","openai/glm-4.7-flash",MODEL].includes(body.model)
      || !Array.isArray(body.messages) || !body.messages.length || body.messages.length>16
      || body.messages.some(x=>!x || !["system","user","assistant","tool"].includes(x.role)
        || !(typeof x.content==="string" || x.content===null || Array.isArray(x.content)))
      || (body.tools!==undefined && (!Array.isArray(body.tools) || body.tools.length>8))
      || (body.n!==undefined && body.n!==1)) return fail(400,"unsupported_public_coding_request");
  let budget;
  try {
    const guard=env.PLENUM_REPLAY_GUARD.getByName("plenum-public-wake");
    budget=await guard.fetch("https://replay-guard.internal/claim-ai",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({day:new Date().toISOString().slice(0,10), reserve:DAILY_RESERVATION,
        maximum:DAILY_LOCAL_MAX})});
  } catch { return fail(503,"free_ai_usage_guard_unavailable"); }
  if (budget?.status===429) return fail(429,"original_daily_ai_budget_exhausted");
  if (budget?.status!==204) return fail(503,"free_ai_usage_guard_unavailable");
  try {
    const native=await env.AI.run(MODEL,{messages:body.messages,
      ...(Array.isArray(body.tools)?{tools:body.tools}:{}),
      temperature:0,max_tokens:Math.min(1024,Number.isInteger(body.max_tokens)?body.max_tokens:1024)});
    const answer=asOpenAI(native,body);
    return encodeOpenAIResult(answer,body.stream===true);
  } catch {
    return fail(502,"free_model_unavailable_or_invalid_result");
  }
}
