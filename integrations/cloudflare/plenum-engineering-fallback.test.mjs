import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto,createHmac} from "node:crypto";
if (!globalThis.crypto) globalThis.crypto=webcrypto;
import {engineeringFallback,engineeringCadenceProof,eligibleCadenceSlot,resolveScheduledTick,CADENCE_START,CADENCE_END,CRON,SLOT_MS} from "./plenum-engineering-fallback.mjs";
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
    if(url.includes("/pulls?"))return Response.json([]);
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
  assert.equal(f.calls.length,3);
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

test("native timestamp seconds normalize only within the scheduled minute",()=>{
  const start=CADENCE_START+SLOT_MS;
  const tick=(raw,cron=CRON)=>({cron,scheduledTime:raw});
  assert.deepEqual(resolveScheduledTick(tick(start+30_329),start+30_432),
    {slot:start,reason:"NORMALIZED_SCHEDULED_MINUTE"});
  assert.equal(resolveScheduledTick(tick(start+59_999),start+59_999).slot,start);
  assert.equal(resolveScheduledTick(tick(start+60_000),start+60_000).slot,null);
  assert.equal(resolveScheduledTick(tick(start+30_000),start+29_999).slot,null);
  assert.equal(resolveScheduledTick(tick(start+30_000),start+SLOT_MS).slot,null);
  assert.equal(resolveScheduledTick(tick(start+30_000,"* * * * *"),start+31_000).slot,null);
  assert.equal(resolveScheduledTick(tick(String(start)),start+31_000).slot,null);
  assert.equal(resolveScheduledTick(tick(NaN),start+31_000).slot,null);
});
test("jittered native events preserve one canonical reservation and never extend freshness",async()=>{
  const old=Date.now;
  const start=CADENCE_START+SLOT_MS;
  let now=start+31_000;
  Date.now=()=>now;
  try {
    const f=fixture();
    const event=(offset)=>({cron:CRON,scheduledTime:start+offset});
    assert.equal(await engineeringFallback(event(30_329),f.env,{fetcher:f.fetcher}),"DISPATCH_ACCEPTED_NOT_COMPLETED");
    assert.equal(await engineeringFallback(event(30_432),f.env,{fetcher:f.fetcher}),"RESERVATION_REJECTED");
    const writes=f.calls.filter(x=>x.method==="POST");
    assert.equal(writes.length,1);
    assert.equal(JSON.parse(writes[0].body).client_payload.slot,start);
    now=start+SLOT_MS;
    assert.equal(await engineeringFallback(event(30_329),f.env,{fetcher:f.fetcher}),"INVALID_OR_STALE_TICK");
    assert.equal(f.calls.filter(x=>x.method==="POST").length,1);
  } finally {Date.now=old;}
});
test("jittered cadence proof keeps original two reservations and canonical signed payload",async()=>{
  const old=Date.now;
  const start=CADENCE_START+SLOT_MS;
  let now=start+31_000;
  Date.now=()=>now;
  try {
    const f=fixture({closed:true});
    const secret="test-only-cadence-secret-not-production-123456";
    f.env.PLENUM_WEBHOOK_HMAC_SECRET=secret;
    const proof=raw=>engineeringCadenceProof({cron:CRON,scheduledTime:raw},f.env,"NO_APPROVED_BACKLOG",{fetcher:f.fetcher});
    assert.equal(await proof(start+30_329),"CADENCE_RECEIPT_DISPATCHED");
    assert.equal(await proof(start+30_432),"CADENCE_NOT_RESERVED");
    now+=SLOT_MS;
    assert.equal(await proof(start+SLOT_MS+30_329),"CADENCE_RECEIPT_DISPATCHED");
    now+=SLOT_MS;
    assert.equal(await proof(start+2*SLOT_MS+30_329),"CADENCE_NOT_RESERVED");
    assert.equal(f.calls.length,2);
    for(const [i,call] of f.calls.entries()){
      const slot=start+i*SLOT_MS;
      assert.deepEqual(JSON.parse(call.body),{event_type:"plenum_engineering_cadence_proof_v1",
        client_payload:{slot,scope:"cron_observation_only",signature:createHmac("sha256",secret)
          .update("plenum-engineering-cadence-v1."+slot+".cron_observation_only").digest("hex")}});
    }
  } finally {Date.now=old;}
});

test("Workers-compatible redirect policy never follows an authenticated read redirect",async()=>{
  const f=fixture();
  const calls=[];
  const fetcher=async(url,init)=>{
    calls.push({url,init});
    assert.equal(init.redirect,"manual");
    return new Response(null,{status:302,headers:{Location:"https://example.invalid/"}});
  };
  assert.equal(await engineeringFallback(event,f.env,{fetcher}),"READ_UNAVAILABLE");
  assert.equal(calls.length,1);
  assert.equal(f.claims.length,0);
});
test("Workers-compatible dispatch redirect is rejected without retry or forwarding",async()=>{
  const f=fixture();
  const calls=[];
  const fetcher=async(url,init)=>{
    calls.push({url,init});
    assert.equal(init.redirect,"manual");
    if(init.method==="POST")return new Response(null,{status:307,headers:{Location:"https://example.invalid/"}});
    return f.fetcher(url,init);
  };
  assert.equal(await engineeringFallback(event,f.env,{fetcher}),"DISPATCH_UNAVAILABLE");
  assert.equal(await engineeringFallback(event,f.env,{fetcher}),"RESERVATION_REJECTED");
  assert.equal(calls.filter(x=>x.init.method==="POST").length,1);
  assert.ok(calls.every(x=>x.url.startsWith("https://api.github.com/repos/"+repo+"/")));
});
test("cadence dispatch rejects manual redirect and retains atomic reservation",async()=>{
  const old=Date.now;
  let now=CADENCE_START+SLOT_MS;
  Date.now=()=>now;
  try {
    const f=fixture({closed:true});
    f.env.PLENUM_WEBHOOK_HMAC_SECRET="test-only-cadence-secret-not-production-123456";
    let writes=0;
    const fetcher=async(url,init)=>{
      assert.equal(init.redirect,"manual");
      assert.equal(url,"https://api.github.com/repos/"+repo+"/dispatches");
      writes++;
      return new Response(null,{status:308,headers:{Location:"https://example.invalid/"}});
    };
    const event={cron:CRON,scheduledTime:now};
    assert.equal(await engineeringCadenceProof(event,f.env,"NO_APPROVED_BACKLOG",{fetcher}),"CADENCE_DISPATCH_UNAVAILABLE");
    assert.equal(await engineeringCadenceProof(event,f.env,"NO_APPROVED_BACKLOG",{fetcher}),"CADENCE_NOT_RESERVED");
    assert.equal(writes,1);
  } finally {Date.now=old;}
});

test("new approved exact-head backlog is discovered; changed head and foreign PR cannot wake",async()=>{
  const pr={number:12345,state:"open",draft:false,user:{login:"chadkhalil21-svg"},
    head:{ref:"prometheus-new-work",sha:"a".repeat(40),repo:{full_name:repo}},
    base:{ref:"main",repo:{full_name:repo}},
    body:"<!-- plenum-engineering-observe-v1:"+"a".repeat(40)+":New native check:qualification -->"};
  for(const [row,expected] of [[pr,"DISPATCH_ACCEPTED_NOT_COMPLETED"],
    [{...pr,head:{...pr.head,sha:"b".repeat(40)}},"NO_APPROVED_BACKLOG"],
    [{...pr,user:{login:"other"}},"NO_APPROVED_BACKLOG"],
    [{...pr,body:pr.body+"\n"+pr.body},"NO_APPROVED_BACKLOG"]]){
    const f=fixture({closed:true});
    const fetcher=async(url,init)=>url.includes("/pulls?")?Response.json([row]):f.fetcher(url,init);
    assert.equal(await engineeringFallback(event,f.env,{fetcher}),expected);
    assert.equal(f.claims.length,expected==="DISPATCH_ACCEPTED_NOT_COMPLETED"?1:0);
  }
});
