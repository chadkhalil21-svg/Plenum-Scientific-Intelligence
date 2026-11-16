import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import worker, {parsePublicIssueId, PublicWakeReplayGuard} from "./plenum-github-wake-worker.mjs";

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const secret = "plenum-test-HMAC-nonproduction-secret-0123456789";
const github = "fake-token-for-test-not-a-provider-secret";
function replayBinding() {
  const items = new Map();
  const ctx = {storage:{transaction: async (fn) => fn({
    get: async (key) => items.get(key),
    put: async (key, value) => {items.set(key, value);}
  })}};
  const guard = new PublicWakeReplayGuard(ctx);
  return {getByName: (name) => {
    assert.equal(name,"plenum-public-wake");
    return {fetch: (url, opts) => guard.fetch(new Request(url, opts))};
  }};
}
const env = {PLENUM_WEBHOOK_HMAC_SECRET:secret,
  PLENUM_GITHUB_DISPATCH_TOKEN:github,
  PLENUM_REPLAY_GUARD:replayBinding()};
const encoder = new TextEncoder();

async function signed(id, {stamp = Math.floor(Date.now() / 1000)} = {}) {
  const body = JSON.stringify({issue_number:id});
  const key = await crypto.subtle.importKey("raw", encoder.encode(secret),
    {name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC",key,
    encoder.encode(String(stamp) + "." + body)));
  const hex = Array.from(sig,v => v.toString(16).padStart(2,"0")).join("");
  return new Request("https://placeholder.workers.dev/wake",{
    method:"POST",headers:{"X-Plenum-Timestamp":String(stamp),
      "X-Plenum-Signature":"sha256=" + hex,"Content-Type":"application/json"},
    body
  });
}

test("health reports reachable not a running model", async () => {
  const reply=await worker.fetch(new Request("https://placeholder.workers.dev/health"), {});
  assert.equal(reply.status,200);
  assert.equal((await reply.json()).state,"REACHABLE_NOT_A_RUNNING_AGENT");
});

test("isolated preview is health-only even with accidentally configured production-like bindings", async () => {
  const blocked=()=>{throw new Error("preview must not touch a provider or storage");};
  const preview={...env,PLENUM_PREVIEW_ONLY:"true",PLENUM_FREE_AI_ENABLED:"true",
    PLENUM_PRIVATE_MEMORY_HMAC_SECRET:secret,
    PLENUM_REPLAY_GUARD:{getByName:blocked},
    PLENUM_PRIVATE_MEMORY:{getByName:blocked},AI:{run:blocked}};
  const old=globalThis.fetch;
  globalThis.fetch=blocked;
  try {
    for (const request of [
      new Request("https://preview.example/memory-check"),
      new Request("https://preview.example/memory-check.js"),
      new Request("https://preview.example/memory"),
      new Request("https://preview.example/memory/example",{method:"PUT"}),
      new Request("https://preview.example/ai/v1/chat/completions",{method:"POST"}),
      await signed(789),
      new Request("https://preview.example/health",{method:"POST"})
    ]) assert.equal((await worker.fetch(request,preview)).status,404);
    const reply=await worker.fetch(new Request("https://preview.example/health"),preview);
    assert.equal(reply.status,200);
    assert.deepEqual(await reply.json(),{state:"ISOLATED_PREVIEW_HEALTH_ONLY",no_model:true});
  } finally {globalThis.fetch=old;}
});

test("valid signed public issue ID wakes original repo without sending message content",async () => {
  const old=globalThis.fetch, calls=[];
  globalThis.fetch=async (url,init)=>{
    calls.push({url,init});
    return new Response(null,{status:204});
  };
  try {
    const reply=await worker.fetch(await signed(789),env);
    assert.equal(reply.status,202);
    assert.equal((await reply.json()).public_issue,789);
    assert.equal(calls.length,1);
    assert.equal(calls[0].url,
      "https://api.github.com/repos/chadkhalil21-svg/Plenum-Scientific-Intelligence/dispatches");
    const data=JSON.parse(calls[0].init.body);
    assert.deepEqual(data,{event_type:"plenum_public_issue_wakeup",
      client_payload:{issue_number:789}});
    assert.equal(calls[0].init.body.includes(secret),false);
  } finally {globalThis.fetch=old;}
});

test("second valid signed wake for the same issue is rejected without a dispatch",async () => {
  const old = globalThis.fetch, calls=[];
  globalThis.fetch=async (...args) => {
    calls.push(args);
    return new Response(null,{status:204});
  };
  try {
    const scoped = {...env,PLENUM_REPLAY_GUARD:replayBinding()};
    assert.equal((await worker.fetch(await signed(987654),scoped)).status,202);
    const second=await worker.fetch(await signed(987654),scoped);
    assert.equal(second.status,409);
    assert.equal((await second.json()).error,"duplicate_issue_wake");
    assert.equal(calls.length,1);
  } finally {globalThis.fetch=old;}
});

test("missing replay binding fails closed before dispatch",async () => {
  const scoped={PLENUM_WEBHOOK_HMAC_SECRET:secret,
    PLENUM_GITHUB_DISPATCH_TOKEN:github};
  assert.equal((await worker.fetch(await signed(867530),scoped)).status,503);
});

test("a replay body completed after the lock expires is rejected as stale",async () => {
  const originalNow=Date.now, originalFetch=globalThis.fetch, calls=[];
  let now=1_800_000_000_000;
  Date.now=()=>now;
  globalThis.fetch=async (...args)=>{
    calls.push(args);
    return new Response(null,{status:204});
  };
  try {
    const scoped={...env,PLENUM_REPLAY_GUARD:replayBinding()};
    const first=await signed(765432);
    const headers=first.headers;
    assert.equal((await worker.fetch(first,scoped)).status,202);
    const replay=new Request("https://placeholder.workers.dev/wake",{
      method:"POST",headers,duplex:"half",
      body:new ReadableStream({
        pull(controller) {
          // Body is read only after the entry-time timestamp check;
          // advance beyond the original atomic lock without sleeping.
          now+=301_000;
          controller.enqueue(encoder.encode(JSON.stringify({issue_number:765432})));
          controller.close();
        }
      },{highWaterMark:0})
    });
    assert.equal((await worker.fetch(replay,scoped)).status,403);
    assert.equal(calls.length,1);
  } finally {
    Date.now=originalNow;
    globalThis.fetch=originalFetch;
  }
});

test("signed timestamp becoming stale in transit to the replay guard cannot claim",async () => {
  const originalNow=Date.now, originalFetch=globalThis.fetch, calls=[];
  let now=1_800_000_000_000;
  Date.now=()=>now;
  globalThis.fetch=async (...args)=>{
    calls.push(args);
    return new Response(null,{status:204});
  };
  try {
    const binding=replayBinding();
    const scoped={...env,PLENUM_REPLAY_GUARD:{getByName(name) {
      const original=binding.getByName(name);
      return {fetch(url,opts) {
        now+=121_000;
        return original.fetch(url,opts);
      }};
    }}};
    assert.equal((await worker.fetch(await signed(765433),scoped)).status,403);
    assert.equal(calls.length,0);
    // A new valid request is still accepted; stale admission must not reserve.
    assert.equal((await worker.fetch(await signed(765433),{...env,PLENUM_REPLAY_GUARD:binding})).status,202);
    assert.equal(calls.length,1);
  } finally {
    Date.now=originalNow;
    globalThis.fetch=originalFetch;
  }
});

test("oversized streamed wake body is canceled before the rest is buffered",async () => {
  const originalFetch=globalThis.fetch;
  let reads=0, canceled=false;
  globalThis.fetch=()=>{throw new Error("network should never be used");};
  try {
    const original=await signed(765434);
    const stream=new ReadableStream({
      pull(controller) {
        reads++;
        if (reads===1) controller.enqueue(new Uint8Array(141));
        else controller.close();
      },
      cancel() { canceled=true; }
    },{highWaterMark:0});
    const request=new Request("https://placeholder.workers.dev/wake",{
      method:"POST",headers:original.headers,duplex:"half",body:stream
    });
    assert.equal((await worker.fetch(request,env)).status,403);
    assert.equal(reads,1);
    assert.equal(canceled,true);
  } finally {
    globalThis.fetch=originalFetch;
  }
});

test("invalid signature and expired request cannot dispatch",async () => {
  const old=globalThis.fetch;
  globalThis.fetch=()=>{throw new Error("network should never be used");};
  try {
    let req=await signed(789);
    req.headers.set("X-Plenum-Signature","sha256="+"0".repeat(64));
    assert.equal((await worker.fetch(req,env)).status,403);
    assert.equal((await worker.fetch(await signed(789,{stamp:1000000000}),env)).status,403);
  } finally {globalThis.fetch=old;}
});

test("non-numeric and extra payload fields blocked",() => {
  assert.equal(parsePublicIssueId(JSON.stringify({issue_number:"78"})),null);
  assert.equal(parsePublicIssueId(JSON.stringify({issue_number:2,secret:"bad"})),null);
  assert.equal(parsePublicIssueId(JSON.stringify({issue_number:2})),2);
});

test("no configured owner account cannot pretend success",async () => {
  assert.equal((await worker.fetch(await signed(789),{})).status,503);
});

