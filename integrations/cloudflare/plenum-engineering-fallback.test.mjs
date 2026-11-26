import test from "node:test";
import assert from "node:assert/strict";
import {engineeringFallback,CRON,SLOT_MS} from "./plenum-engineering-fallback.mjs";
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
