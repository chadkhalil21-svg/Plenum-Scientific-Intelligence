import test from "node:test";
import assert from "node:assert/strict";
import { approvedUrl, readOnlyCall, validateCall, ALLOWED_READ_TOOLS } from "./policy.mjs";

test("only exact approved public HTTPS page is navigable", () => {
  assert.equal(approvedUrl("https://example.com/"), true);
  for (const value of [
    "https://example.com.evil.com/", "https://example.com@evil.org/",
    "http://example.com/", "https://127.0.0.1/", "https://localhost/",
    "https://169.254.169.254/latest/", "file:///etc/passwd",
    "https://example.com:8080/", "https://example.com/#private",
    "https://example.com/?query=secret", "https://example.com/path",
    "https://example.com/\nInjected: X", "https://news.mit.edu/",
  ]) assert.equal(approvedUrl(value), false, value);
});

test("never let planner invoke arbitrary browser tools", async () => {
  assert.deepEqual(ALLOWED_READ_TOOLS, ["browser_navigate", "browser_snapshot", "browser_close"]);
  for (const forbidden of ["browser_click","browser_type","browser_fill_form",
    "browser_file_upload","browser_run_code","browser_evaluate", "browser_navigate_back"]) {
    assert.throws(() => validateCall(forbidden, {}));
  }
  assert.throws(() => validateCall("browser_navigate", {url:"https://evil.org/"}));
  assert.throws(() => validateCall("browser_navigate", {url:"https://example.com/", ignore:true}));
  assert.throws(() => validateCall("browser_snapshot", {code:"alert(1)"}));
});

test("gateway delegates only allowed calls, fails closed on MCP errors", async () => {
  const used=[];
  const client={
    async callTool(msg) { used.push(msg); return { isError: false, content: [{type:"text",text:"Safe"}] }; }
  };
  const r=await readOnlyCall(client, "browser_navigate", {url:"https://example.com/"});
  assert.equal(r.content[0].text, "Safe");
  assert.deepEqual(used,[{name:"browser_navigate",arguments:{url:"https://example.com/"}}]);
  await assert.rejects(readOnlyCall({callTool:async()=>({isError:true})},"browser_snapshot",{}));
});
