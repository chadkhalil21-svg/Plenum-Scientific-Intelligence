/*
 * Zero-dependency readback page for the ALREADY EXISTING Plenum Worker.
 * Browser signs locally; the original secret is never transmitted or stored.
 * No external analytics, CDN, remote JS, cookies, or paid services.
 */
const HTML = String.raw`<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plenum Private Memory | Owner Verification</title>
<style>
:root{font:16px/1.45 system-ui,-apple-system,sans-serif;color-scheme:light dark}
body{max-width:42rem;margin:2.5rem auto;padding:0 1.1rem}
h1{font-size:1.55rem;margin-bottom:.5rem}
p{margin:.6rem 0 1rem}
label{display:block;font-weight:650;margin:.9rem 0 .35rem}
input{display:block;width:100%;padding:.7rem;font:inherit;box-sizing:border-box}
button{padding:.78rem 1rem;margin:.7rem .55rem .5rem 0;font:inherit;cursor:pointer;border-radius:.5rem}
button:disabled{opacity:.5;cursor:wait}
#status{white-space:pre-wrap;overflow-wrap:anywhere;padding:1rem;border:1px solid #888;border-radius:.5rem;min-height:2.2rem}
small{display:block;margin-top:1rem}
</style></head><body>
<main>
<h1>Plenum private memory — owner verification</h1>
<p>Use only at <strong>plenum-public-wake.chadkhalil21.workers.dev</strong>.
This page signs requests entirely in this browser. Thy secret is neither sent
to Cloudflare in plaintext nor stored by this page.</p>
<label for="secret">Private memory secret (from thy password manager)</label>
<input id="secret" type="password" autocomplete="off" spellcheck="false" autocapitalize="none"
  minlength="32" placeholder="Paste the separate private-memory secret">
<button id="write" type="button">Write harmless proof, then read</button>
<button id="read" type="button">Read existing proof (later session)</button>
<div id="status" role="status" aria-live="polite">No memory operation performed yet.</div>
<small>The proof contains no personal messages or credentials. Close or reload this
page to discard the entered secret. The canonical Google Drive ledger remains authoritative.
This verifies only our Cloudflare memory, not ChatGPT-wide automatic recall.</small>
</main>
<script defer src="/memory-check.js"></script>
</body></html>`;

const SCRIPT = String.raw`"use strict";
/* No external scripts. No cookies, logging, local/session storage or telemetry. */
(() => {
  const key = "plenum:continuity-proof";
  const source = "https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/483";
  const summary = "Source-linked nonsensitive memory connectivity proof. No private conversations.";
  const input = document.getElementById("secret");
  const status = document.getElementById("status");
  const writeButton = document.getElementById("write");
  const readButton = document.getElementById("read");
  const encoder = new TextEncoder();

  function show(message) { status.textContent = message; }
  function hex(bytes) { return Array.from(bytes, b => b.toString(16).padStart(2, "0")).join(""); }
  async function signed(method, path, raw, cryptoKey) {
    const stamp = String(Date.now());
    const signedText = [method, path, stamp, raw].join("\n");
    const digest = await crypto.subtle.sign("HMAC", cryptoKey, encoder.encode(signedText));
    const response = await fetch(path, {
      method,
      headers: {
        "x-plenum-memory-time": stamp,
        "x-plenum-memory-signature": "sha256=" + hex(new Uint8Array(digest)),
        "accept": "application/json",
        ...(method === "POST" ? {"content-type": "application/json"} : {})
      },
      ...(method === "POST" ? {body:raw} : {}),
      cache:"no-store", credentials:"omit", referrerPolicy:"no-referrer", redirect:"error"
    });
    const answer = await response.json().catch(() => ({}));
    return {code:response.status, data:answer};
  }
  async function retrieve(cryptoKey) {
    return signed("GET", "/memory/" + key, "", cryptoKey);
  }
  async function execute(mode) {
    const secret = input.value;
    input.value = "";
    if (secret.length < 32) {
      show("Enter the separate private-memory secret (32 characters minimum).");
      return;
    }
    if (!crypto?.subtle) {
      show("This browser requires a secure HTTPS context for local signing.");
      return;
    }
    writeButton.disabled = readButton.disabled = true;
    show("Signing locally and checking the existing private memory.");
    try {
      const cryptoKey = await crypto.subtle.importKey(
        "raw", encoder.encode(secret), {name:"HMAC",hash:"SHA-256"}, false, ["sign"]);
      // Credentials have never left this page; only HMAC signature is sent.
      const before = await retrieve(cryptoKey);
      if (mode === "read") {
        if (before.code === 200 && Number.isSafeInteger(before.data.revision)) {
          show("OWNER PRIVATE READ ACCEPTED\nRevision: " + before.data.revision +
            "\nSource: " + before.data.source +
            "\nRecorded: " + before.data.stored_at +
            "\nThis is a readback, not universal ChatGPT Memory.");
        } else if (before.code === 404) {
          show("Private access accepted, but no proof record has been written yet.");
        } else {
          show("Read not verified. HTTP status: " + before.code +
            ". A 403 may mean an incorrect private-memory secret; 503 indicates unavailable configuration.");
        }
        return;
      }
      const revision = before.code === 404 ? 0 :
        (before.code === 200 && Number.isSafeInteger(before.data.revision)
          ? before.data.revision : null);
      if (revision === null) {
        show("Private access not verified. HTTP status: " + before.code +
          ". Do not change existing secrets without new evidence.");
        return;
      }
      const body = JSON.stringify({
        key, summary, source, level:"VERIFIED",
        observed_at:new Date().toISOString(),
        expected_revision:revision
      });
      const put = await signed("POST","/memory",body,cryptoKey);
      if (put.code !== 200 || put.data.revision !== revision+1) {
        show("Write not verified. HTTP status: " + put.code +
          ". No completion is claimed.");
        return;
      }
      const after = await retrieve(cryptoKey);
      if (after.code === 200 && after.data.revision === revision+1 &&
          after.data.summary === summary && after.data.source === source) {
        show("OWNER PRIVATE WRITE + READ VERIFIED\nRevision: " + after.data.revision +
          "\nSource: " + source +
          "\nFor CROSS-SESSION proof, close this page, open it afresh, and select Read existing proof.");
      } else {
        show("Write acknowledged; independent readback NOT verified. Read HTTP status: " + after.code);
      }
    } catch {
      show("No verified result. Check HTTPS/connection and the existing deployed Worker. " +
        "The private secret has not been saved by this page.");
    } finally {
      // Only signed messages were sent; no secret persists in page controls.
      writeButton.disabled = readButton.disabled = false;
    }
  }
  writeButton.addEventListener("click", () => execute("write"));
  readButton.addEventListener("click", () => execute("read"));
})();`;

const SECURE_HEADERS = {
  "Cache-Control":"no-store",
  "X-Content-Type-Options":"nosniff",
  "Referrer-Policy":"no-referrer",
  "X-Frame-Options":"DENY",
  "Cross-Origin-Resource-Policy":"same-origin"
};

export function ownerMemoryCheckPage() {
  return new Response(HTML, {status:200,headers:{
    ...SECURE_HEADERS,
    "Content-Type":"text/html; charset=utf-8",
    "Content-Security-Policy":"default-src 'none'; script-src 'self'; " +
      "connect-src 'self'; style-src 'unsafe-inline'; img-src 'none'; " +
      "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
  }});
}

export function ownerMemoryCheckScript() {
  return new Response(SCRIPT,{status:200,headers:{
    ...SECURE_HEADERS, "Content-Type":"application/javascript; charset=utf-8"
  }});
}
