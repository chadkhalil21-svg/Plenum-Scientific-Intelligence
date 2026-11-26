import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto,createHmac} from "node:crypto";
if (!globalThis.crypto) globalThis.crypto=webcrypto;
import {engineeringFallback,engineeringCadenceProof,eligibleCadenceSlot,CADENCE_START,CADENCE_END,CRON,SLOT_MS} from "./plenum-engineering-fallback.mjs";
import {PublicWakeReplayGuard} from "./plenum-github-wake-worker.mjs";
const repo="chadkhalil21-svg/Plenum-Scientific-Intelligence";
const slot=Math.floor(Date.now()/SLOT_MS)*SLOT_MS;
function fixture({closed=false,unavailable=false,dispatchStatus=204}={}) {
  const calls=[],claims=[],items=new Map();
  const guard=new PublicWakeReplayGuard({storage:{transaction:fn=>fn({
    get:async key=>items.get(key),put:async (key,value)=>items.set(key,value)
  })}});
  const env={PLENUM_ENGINEERING_FALLBACK_ENABLED:"true",PLENUM_GITHUB_DISPATCH_TOKEN:"fake-test-token",
    PLENUM_REPLAY_GUARD:{getByName(name){
      assert.equal(name,"plenum-engineering-fallback");
      return {fetch(url,init){claims.push(url);return guard.fetch(new Request(url,init));}};
    }}};
  const fetcher=async(url,init)=>{
    calls.push({url,method:init.method,body:init.body});
    if(url.endsWith("/dispatches"))return new Response(null,{status:dispatchStatus});
    if(unavailable)return new Response(null,{status:503});
    const n=Number(url.split("/").at(-1));
    return Response.json({number:n,state:closed?"closed":"open",user:{login:"chadkhalil21-svg"},
      head:{ref:n===935?"prometheus-hyperframes-local-qualification":"prometheus-accepted-upstream-evidence-registry",sha:"a".repeat(40),repo:{full_name:repo}},
      base:{ref:"main",repo:{full_name:repo}}});
  };
  return {env,fetcher,calls,claims};
}
const event={cron:CRON,scheduledTime:slot};
test("one dispatch per current slot; no replay even when response fails",async()=>{
  const f=fixture({dispatchStatus:502});
  assert.equal(await engineeringFallback(event,f.env,{fetcher:f.fetcher}),"DISPATCH_UNAVAILABLE");
  assert.equal(await engineeringFallback(event,f.env,{fetcher:f.fetcher}),"RESERVATION_REJECTED");
  const dispatch=f.calls.filter(x=>x.method==="POST");
  assert.equal(dispatch.length,1);
  assert.deepEqual(JSON.parse(dispatch[0].body),{event_type:"plenum_engineering_backlog_tick_v1",client_payload:{slot}});
});
test("approved open backlog dispatch is bounded",async()=>{
  const f=fixture();
  assert.equal(await engineeringFallback(event,f.env,{fetcher:f.fetcher}),"DISPATCH_ACCEPTED_NOT_COMPLETED");
  assert.equal(f.calls.length,3);
  assert.equal(f.claims.length,1);
});
test("closed approved backlog never provisions a runner",async()=>{
  const f=fixture({closed:true});
  assert.equal(await engineeringFallback(event,f.env,{fetcher:f.fetcher}),"NO_APPROVED_BACKLOG");
  assert.equal(f.calls.length,2);
  assert.equal(f.claims.length,0);
});
test("preview, stale slot and unavailable reads fail closed",async()=>{
  const f=fixture();
  assert.equal(await engineeringFallback(event,{...f.env,PLENUM_PREVIEW_ONLY:"true"},{fetcher:f.fetcher}),"DISABLED");
  assert.equal(await engineeringFallback(event,f.env,{fetcher:f.fetcher,clock:()=>slot+SLOT_MS}),"INVALID_OR_STALE_TICK");
  assert.equal(f.calls.length,0);
  const g=fixture({unavailable:true});
  assert.equal(await engineeringFallback(event,g.env,{fetcher:g.fetcher}),"READ_UNAVAILABLE");
  assert.equal(g.claims.length,0);
});

test("two authenticated cadence receipts only, including ambiguous failure; never repeat",async()=>{
  const old=Date.now;
  let now=CADENCE_START+SLOT_MS;
  Date.now=()=>now;
  try {
    const f=fixture({closed:true,dispatchStatus:502});
    const secret="test-only-cadence-secret-not-production-123456";
    f.env.PLENUM_WEBHOOK_HMAC_SECRET=secret;
    const tick=()=>({cron:CRON,scheduledTime:now});
    assert.equal(await engineeringCadenceProof(tick(),f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_DISPATCH_UNAVAILABLE");
    assert.equal(await engineeringCadenceProof(tick(),f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_NOT_RESERVED");
    now+=SLOT_MS;
    assert.equal(await engineeringCadenceProof(tick(),f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_DISPATCH_UNAVAILABLE");
    now+=SLOT_MS;
    assert.equal(await engineeringCadenceProof(tick(),f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_NOT_RESERVED");
    assert.equal(f.calls.length,2);
    for (const [i,call] of f.calls.entries()) {
      const slot=CADENCE_START+(i+1)*SLOT_MS;
      assert.deepEqual(JSON.parse(call.body),{event_type:"plenum_engineering_cadence_proof_v1",
        client_payload:{slot,scope:"cron_observation_only",signature:createHmac("sha256",secret)
          .update("plenum-engineering-cadence-v1."+slot+".cron_observation_only").digest("hex")}});
      assert.equal(call.body.includes(secret),false);
    }
  } finally {Date.now=old;}
});
test("cadence observation disabled in previews, outside window or when approved work exists",async()=>{
  const old=Date.now;
  let now=CADENCE_START+SLOT_MS;
  Date.now=()=>now;
  try {
    const f=fixture({closed:true});
    f.env.PLENUM_WEBHOOK_HMAC_SECRET="test-only-cadence-secret-not-production-123456";
    const tick=()=>({cron:CRON,scheduledTime:now});
    for (const env of [{...f.env,PLENUM_PREVIEW_ONLY:"true"},{...f.env,PLENUM_WEBHOOK_HMAC_SECRET:""},{...f.env,PLENUM_ENGINEERING_FALLBACK_ENABLED:"false"}])
      assert.equal(await engineeringCadenceProof(tick(),env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_NOT_ELIGIBLE");
    assert.equal(await engineeringCadenceProof(tick(),f.env,"DISPATCH_ACCEPTED_NOT_COMPLETED",{fetcher:f.fetcher}),"CADENCE_NOT_ELIGIBLE");
    assert.equal(await engineeringCadenceProof({cron:CRON,scheduledTime:now-SLOT_MS},f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_NOT_ELIGIBLE");
    now=CADENCE_END;
    assert.equal(eligibleCadenceSlot(now),false);
    assert.equal(await engineeringCadenceProof(tick(),f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher}),"CADENCE_NOT_ELIGIBLE");
    assert.equal(f.claims.length,0);
    assert.equal(f.calls.length,0);
  } finally {Date.now=old;}
});
