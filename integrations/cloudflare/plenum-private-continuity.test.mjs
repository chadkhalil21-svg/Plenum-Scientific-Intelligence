import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import originalWake from "./plenum-github-wake-worker.mjs";
import {PrivateContinuityMemory} from "./plenum-private-continuity.mjs";

if(!globalThis.crypto) globalThis.crypto=webcrypto;
const secret="local-nonproduction-private-memory-signing-secret-12345";
const store=new Map();
const ctx={storage:{
  get:async key=>store.get(key),
  transaction:async fn=>fn({
    get:async key=>store.get(key),
    put:async(key,value)=>{store.set(key,value)}
  })
}};
const object=new PrivateContinuityMemory(ctx);
const configured={
  PLENUM_PRIVATE_MEMORY_HMAC_SECRET:secret,
  PLENUM_PRIVATE_MEMORY:{getByName:name=>{
    assert.equal(name,"plenum-private-continuity");
    return {fetch:(url,options)=>object.fetch(new Request(url,options))};
  }}
};
const record={
 key:"american-rider:apple-build-60",
 summary:"Provider screenshot confirms the updated review state with the original build retained.",
 source:"https://github.com/chadkhalil21-svg/American-Rider-Commercial/issues/451",
 observed_at:"2026-11-12T20:09:00-05:00",
 level:"VERIFIED",
 expected_revision:0
};
async function signed(method,path,body="",overrideSecret=secret){
  const timestamp=String(Date.now());
  const key=await crypto.subtle.importKey("raw",new TextEncoder().encode(overrideSecret),
    {name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const data=[method,path,timestamp,body].join("\n");
  const sig=new Uint8Array(await crypto.subtle.sign("HMAC",key,new TextEncoder().encode(data)));
  const hex=Array.from(sig,x=>x.toString(16).padStart(2,"0")).join("");
  return new Request("https://public.wake.dev"+path,{
    method,
    headers:{"x-plenum-memory-time":timestamp,"x-plenum-memory-signature":"sha256="+hex},
    ...(method==="POST"?{body}: {})
  });
}

test("same original public wake remains unchanged",async()=>{
  const response=await originalWake.fetch(new Request("https://public.wake.dev/health"),{});
  assert.equal(response.status,200);
  assert.equal((await response.json()).state,"REACHABLE_NOT_A_RUNNING_AGENT");
});
test("missing private secret and binding fail closed",async()=>{
  const r=await originalWake.fetch(await signed("GET","/memory/missing"),{});
  assert.equal(r.status,503);
});
test("unsigned and bad signature cannot read or write",async()=>{
  assert.equal((await originalWake.fetch(
    new Request("https://public.wake.dev/memory/example"),configured)).status,403);
  assert.equal((await originalWake.fetch(
    await signed("GET","/memory/example","","not-the-private-secret-but-32-char"),configured)).status,403);
});
test("only owner HMAC can write and later read persistent revision",async()=>{
  const put=await originalWake.fetch(await signed("POST","/memory",JSON.stringify(record)),configured);
  assert.equal(put.status,200);
  assert.equal((await put.json()).revision,1);
  const read=await originalWake.fetch(await signed("GET","/memory/"+record.key),configured);
  const data=await read.json();
  assert.equal(data.revision,1);
  assert.equal(data.level,"VERIFIED");
  assert.equal(data.summary,record.summary);
});
test("stale updates and replay do not overwrite newer provider evidence",async()=>{
  const stale=await originalWake.fetch(await signed("POST","/memory",JSON.stringify(record)),configured);
  assert.equal(stale.status,409);
  assert.equal((await stale.json()).error,"stale_revision");
  const next={...record,expected_revision:1,summary:"Original review source later updated, history remains available to private storage."};
  assert.equal((await originalWake.fetch(await signed("POST","/memory",JSON.stringify(next)),configured)).status,200);
  const actual=await (await originalWake.fetch(await signed("GET","/memory/"+record.key),configured)).json();
  assert.equal(actual.revision,2);
  assert.equal(store.get("history:"+record.key+":1").revision,1);
  assert.equal(store.get("history:"+record.key+":2").revision,2);
});
test("opaque body, arbitrary fields, malformed HTTPS source rejected",async()=>{
  const bad={...record,expected_revision:2,source:"https://user:pw@example.net/abc"};
  assert.equal((await originalWake.fetch(await signed("POST","/memory",JSON.stringify(bad)),configured)).status,400);
  const overshare={...record,expected_revision:2,private_token:"must-never-write"};
  assert.equal((await originalWake.fetch(await signed("POST","/memory",JSON.stringify(overshare)),configured)).status,400);
  const unknown=await originalWake.fetch(await signed("GET","/memory/absent"),configured);
  assert.equal(unknown.status,404);
});
