import test from "node:test";
import assert from "node:assert/strict";
import originalWorker from "./plenum-github-wake-worker.mjs";

test("owner verification page is on ORIGINAL existing Worker, not a new service", async () => {
  const result = await originalWorker.fetch(new Request("https://plenum-public-wake.chadkhalil21.workers.dev/memory-check"),{});
  assert.equal(result.status,200);
  assert.match(result.headers.get("Content-Type"),/text\/html/);
  assert.match(result.headers.get("Content-Security-Policy"),/connect-src 'self'/);
  assert.match(result.headers.get("Content-Security-Policy"),/frame-ancestors 'none'/);
  assert.equal(result.headers.get("Cache-Control"),"no-store");
  const text=await result.text();
  assert.match(text,/Private Memory|private memory/i);
  assert.match(text,/type="password"/);
  assert.match(text,/memory-check\.js/);
  assert.doesNotMatch(text,/PLENUM_PRIVATE_MEMORY_HMAC_SECRET/);
});

test("browser signer sends only HMAC and memory probe metadata", async () => {
  const result=await originalWorker.fetch(new Request("https://plenum-public-wake.chadkhalil21.workers.dev/memory-check.js"),{});
  assert.equal(result.status,200);
  const body=await result.text();
  assert.match(result.headers.get("Content-Type"),/javascript/);
  assert.doesNotThrow(()=>new Function(body));
  assert.match(body,/crypto\.subtle\.sign/);
  assert.match(body,/credentials:"omit"/);
  assert.match(body,/\/memory\//);
  assert.doesNotMatch(body, /localStorage|sessionStorage|document\.cookie|console\.log|fetch\s*\(\s*["']https:\/\//);
});

test("no unauthenticated memory read; health and wake semantics untouched", async () => {
  const get=await originalWorker.fetch(
    new Request("https://plenum-public-wake.chadkhalil21.workers.dev/memory/plenum:continuity-proof"),{
      PLENUM_PRIVATE_MEMORY_HMAC_SECRET:"a".repeat(48),
      PLENUM_PRIVATE_MEMORY:{getByName(){throw new Error("must not reach private store")}}
    });
  assert.equal(get.status,403);
  const health=await originalWorker.fetch(new Request("https://plenum-public-wake.chadkhalil21.workers.dev/health"),{});
  assert.equal(health.status,200);
  assert.equal((await health.json()).state,"REACHABLE_NOT_A_RUNNING_AGENT");
  const bad=await originalWorker.fetch(new Request("https://plenum-public-wake.chadkhalil21.workers.dev/memory-check",{method:"POST"}),{});
  assert.equal(bad.status,404);
});
