import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import worker from "./plenum-github-wake-worker.mjs";
import {PrivateContinuityMemory} from "./plenum-private-continuity.mjs";
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const company="11111111-1111-4111-8111-111111111111";
const mission="22222222-2222-4222-8222-222222222222";
const issue="33333333-3333-4333-8333-333333333333";
const owner="fixture-owner-private-secret-not-for-runtime-012345";
const secret="fixture-paperclip-scoped-secret-not-production-0123";
const path="/paperclip-checkpoints/"+company+"/"+mission+"/intelligence";
const values=new Map(),names=[];
const object=new PrivateContinuityMemory({storage:{get:async k=>values.get(k),
  transaction:async fn=>fn({get:async k=>values.get(k),put:async(k,v)=>values.set(k,v)})}});
const env={PLENUM_PRIVATE_MEMORY_HMAC_SECRET:owner,
  PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET:secret,PLENUM_PAPERCLIP_CHECKPOINT_SCOPE:company+"/"+mission,
  PLENUM_PRIVATE_MEMORY:{getByName:name=>{names.push(name);return {fetch:(url,opts)=>object.fetch(new Request(url,opts))};}}};
async function signed(method,target,value,key=secret,stamp=String(Date.now())){
  const raw=value===undefined?"":JSON.stringify(value);
  const k=await crypto.subtle.importKey("raw",new TextEncoder().encode(key),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const sig=Buffer.from(await crypto.subtle.sign("HMAC",k,new TextEncoder().encode([method,target,stamp,raw].join("\n")))).toString("hex");
  return new Request("https://test.example"+target,{method,headers:{"x-plenum-memory-time":stamp,
    "x-plenum-memory-signature":"sha256="+sig},...(value===undefined?{}:{body:raw})});
}
test("runtime scope cannot access private memory, other missions, previews or unsigned routes",async()=>{
  assert.equal((await worker.fetch(await signed("GET","/memory/private"),env)).status,403);
  assert.equal((await worker.fetch(await signed("GET",path,undefined,owner),env)).status,403);
  assert.equal((await worker.fetch(await signed("GET",path.replace(mission,issue)),env)).status,403);
  assert.equal((await worker.fetch(await signed("GET",path),{...env,PLENUM_PREVIEW_ONLY:"true"})).status,404);
  assert.equal((await worker.fetch(new Request("https://test.example"+path),env)).status,403);
  const stale=await worker.fetch(await signed("GET",path,undefined,secret,String(Date.now()-121000)),env);
  assert.equal(stale.status,403);
  assert.deepEqual(await stale.json(),{error:"unauthorized_or_stale"});
  const invalid=await worker.fetch(await signed("GET",path,undefined,"wrong-fixture-secret-not-production-12345"),env);
  assert.equal(invalid.status,403);
  assert.deepEqual(await invalid.json(),{error:"unauthorized_or_stale"});
  assert.equal((await worker.fetch(await signed("GET",path,undefined,owner),{...env,PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET:owner})).status,403);
  assert.equal(names.length,0);
});
test("bounded reserve, compare-and-swap, replay denial, completion and readback",async()=>{
  const first={issue,attempt:1,state:"reserved",sha256:null,expected_revision:0};
  const put=async value=>worker.fetch(await signed("POST",path,value),env);
  assert.equal((await put({...first,private_text:"forbidden"})).status,400);
  assert.equal((await put({...first,attempt:2})).status,409);
  assert.equal((await put(first)).status,200);
  assert.equal((await put(first)).status,409);
  assert.equal((await put({...first,attempt:2,expected_revision:1})).status,200);
  assert.equal((await put({...first,attempt:3,expected_revision:2})).status,400);
  const done={...first,attempt:2,expected_revision:2,state:"completed",sha256:"a".repeat(64)};
  assert.equal((await put(done)).status,200);
  assert.equal((await put({...done,expected_revision:3,sha256:"b".repeat(64)})).status,409);
  const actual=await(await worker.fetch(await signed("GET",path),env)).json();
  assert.deepEqual(actual,{issue,attempt:2,state:"completed",sha256:"a".repeat(64),revision:3});
  assert.ok(names.every(n=>n==="plenum-paperclip:"+company+":"+mission));
  console.log("SCOPED CHECKPOINT PASS two reservations, immutable completion, separate DO instance");
});
