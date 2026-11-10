"""Privately authenticated browser view for one-time website sign-ins.

The *human*, not ChatGPT, clicks and types into real websites through a
short-lived Chromium stream. Credentials never enter ChatGPT or public GitHub.
No model-exposed remote click/fill API is added by this module.
"""
import asyncio
import base64
import os
import secrets
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from .engine import safe_url, public_dns_only
from .iap_identity import verify_owner_token
from .owner_auth0 import active as auth0_active, verified_session as auth0_verified_session
from .owner_console import require_verified_owner
from .private_profiles import BrowserProfileStore


def filter_site_storage(state,site_origin):
    """Keep only the selected HTTPS site's encrypted cookies/localStorage/IndexedDB.

    Never retain Google/other IdP origins. IndexedDB may contain authentication
    tokens, so it is treated as sensitive session state, never model output.
    """
    parsed=urlsplit(site_origin)
    h=parsed.hostname
    if (parsed.scheme!="https" or not h or parsed.path or parsed.query
            or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("Expected exact HTTPS site origin")
    def same_site(cookie):
        d=str(cookie.get("domain","")).lower().lstrip(".")
        return d==h or h.endswith("."+d)
    return {
        "cookies":[c for c in state.get("cookies",[]) if same_site(c)],
        # Exact origin, not hostname-only: never copy an insecure http:
        # origin or a different port into the owner's HTTPS session.
        "origins":[o for o in state.get("origins",[])
                   if isinstance(o,dict) and o.get("origin")==site_origin],
    }


async def _focused_editable_kind(page):
    """Return only an editable field class; never expose DOM text or typed secrets."""
    return await page.evaluate("""() => {
      const el = document.activeElement;
      if (!el || el.disabled || el.readOnly) return "none";
      if (el.isContentEditable || el.tagName === "TEXTAREA") return "text";
      if (el.tagName !== "INPUT") return "none";
      if (el.type === "password") return "password";
      return ["text", "email", "search", "url", "tel", "number"].includes(el.type)
          ? "text" : "none";
    }""")


def _persist_encrypted_site_profile(*, owner_id, origin, state):
    """Write only a site-scoped storage state; no secrets or profile IDs in output."""
    store=BrowserProfileStore.from_environment()
    generation=store.current_generation(owner=owner_id,origin=origin)
    if generation is None:
        store.save_new(owner=owner_id,origin=origin,state=state,ttl_seconds=86400)
    else:
        store.replace_if_current(owner=owner_id,origin=origin,state=state,
                                 expected_generation=generation,ttl_seconds=86400)


def login_html(nonce):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Computer · Secure Website Login</title>
    <style>body{font:16px system-ui;margin:16px auto;padding:0 12px;max-width:1060px}
    button,input{font:inherit;padding:9px;margin:3px}
    input#url{width:78%;max-width:720px}input#text{width:64%;max-width:680px}
    canvas{border:1px solid gray;width:100%;max-width:1024px;background:#eee;
    touch-action:manipulation;cursor:crosshair}
    #status,#field-status{white-space:pre-wrap}h1{font-size:23px}</style></head><body>
    <h1>Computer · Private Website Sign-in</h1>
    <p>Open the actual website thou ownest or art authorized to use.
    This owner-only Chromium canvas is the LIVE browser picture; it cannot
    presently stream directly into an ordinary ChatGPT chat.</p>
    <p>Sign in or create a website account personally, and use its own
    <strong>Continue with Google</strong> button only when offered. Google may
    block automatic or embedded sign-ins, so a supported external browser
    or site-specific connection may be necessary. Use a password manager
    to generate a distinct password for websites without Google sign-in.
    Never share credentials or recovery codes in ChatGPT or GitHub.</p>
    <p>After a successful website sign-in, choose
    <strong>Save this website login</strong> to encrypt its site-specific
    session for later approved Plenum tasks. The encrypted copy may include
    this website's cookies, local storage and IndexedDB authentication data,
    but never your Google password or other websites' login data.
    Saved state can expire and doth not bypass future MFA. A saved session
    is not an account password.</p>
    <label>Website <input id="url" type="url" placeholder="https://website.example/login"
    required maxlength="1200" autocomplete="off"></label>
    <button id="open">Open secure browser</button>
    <p id="status" role="status">Not connected</p>
    <canvas width="1024" height="720" id="display" tabindex="0" aria-label="Remote Chromium view: tap or click a field to select it"></canvas>
    <p id="field-status" role="status">Tap a field in the picture to select it. The private text box will not clear until typing is confirmed.</p>
    <p><input type="password" id="text" autocomplete="off"
    placeholder="Type privately into selected website field">
    <button id="type" disabled>Type</button>
    <button id="enter" disabled>Enter</button>
    <button id="tab" disabled>Tab</button>
    <button id="reload" disabled>Reload</button>
    <button id="save" disabled>Save this website login</button>
    <button id="close">Close</button></p>
    <script nonce="__NONCE__">
    let ws=null,ready=false,selected="none",pendingText=null,frameNumber=0;
    let lastTouchAt=0,saveInFlight=false;
    const canvas=document.getElementById("display"),
      ctx=canvas.getContext("2d"),
      status=document.getElementById("status"),
      fieldStatus=document.getElementById("field-status"),
      textInput=document.getElementById("text"),
      typeButton=document.getElementById("type");
    function updateTypingEnabled(){
      typeButton.disabled=!ready||selected==="none"||pendingText!==null;
      for(const id of ["enter","tab","reload"]){
        document.getElementById(id).disabled=!ready;
      }
      document.getElementById("save").disabled=!ready||saveInFlight;
    }
    function clearStalePreview(){
      ++frameNumber;
      ctx.clearRect(0,0,1024,720);
    }
    function send(m){
      if(ws&&ws.readyState===WebSocket.OPEN&&ready){
        ws.send(JSON.stringify(m));return true;
      }
      fieldStatus.textContent="No live browser connection. Reopen secure browser to resume; previously typed website fields cannot be assumed saved.";
      return false;
    }
    document.getElementById("open").onclick=()=>{
      if(ws)ws.close();
      clearStalePreview();
      const u=new URL("/owner/live",location.origin);
      u.protocol=location.protocol==="https:"?"wss:":"ws:";
      u.searchParams.set("site",document.getElementById("url").value.trim());
      const connection=new WebSocket(u);
      ws=connection;ready=false;selected="none";pendingText=null;saveInFlight=false;
      updateTypingEnabled();
      fieldStatus.textContent="Waiting for live browser picture.";
      let connected=false,serverStopped=false,openedAt=null;
      status.textContent="Connecting to private browser...";
      connection.onopen=()=>{
        if(ws!==connection)return;
        connected=true;openedAt=Date.now();
        status.textContent="Connected. Starting private Chromium...";
      };
      connection.onerror=()=>{
        if(ws!==connection||serverStopped)return;
        status.textContent="Secure browser stream unavailable; check sign-in and connectivity.";
      };
      connection.onclose=e=>{
        if(ws!==connection)return;
        ready=false;selected="none";pendingText=null;saveInFlight=false;updateTypingEnabled();
        clearStalePreview();
        const elapsed=openedAt===null?"":", after "+Math.round((Date.now()-openedAt)/1000)+" seconds";
        if(!serverStopped){
          if(e.code===4403||(!connected&&e.code===1006))
            status.textContent="Browser sign-in or connection was rejected (code "+e.code+"). Sign in again if needed.";
          else if(e.code===1000)
            status.textContent="Private browser session closed"+elapsed+".";
          else
            status.textContent="Private browser disconnected"+elapsed+" (code "+e.code+").";
        }
        fieldStatus.textContent="The previous browser image has been cleared. Reopen secure browser for a new session; unsaved website fields are not retained.";
      };
      connection.onmessage=e=>{
        if(ws!==connection)return;
        const m=JSON.parse(e.data);
        if(m.type==="status"){
          status.textContent=m.message;
          if(m.failure===true){
            serverStopped=true;ready=false;selected="none";saveInFlight=false;updateTypingEnabled();
            clearStalePreview();
            fieldStatus.textContent="Browser operation ended; previous image cleared. Reopen secure browser.";
          }
        }
        if(m.type==="save_result"){
          saveInFlight=false;
          updateTypingEnabled();
          status.textContent=m.message||"Private session save did not complete.";
          fieldStatus.textContent=m.ok===true
            ?"Website state stored encrypted. Login restoration is NOT yet verified; use Saved Website Sessions."
            :"Browser remains open. Saving was not confirmed; do not assume this login is stored.";
        }
        if(m.type==="ack"&&m.action==="click"){
          selected=["text","password"].includes(m.field)?m.field:"none";
          fieldStatus.textContent=selected==="password"?"Password field selected. Type privately below."
            :selected==="text"?"Text field selected. Type privately below."
            :"Website click received. For typing, tap the center of a text or password input.";
          updateTypingEnabled();
        }
        if(m.type==="ack"&&m.action==="type"){
          if(m.ok===true){
            if(pendingText!==null&&textInput.value===pendingText)textInput.value="";
            fieldStatus.textContent="Text entered into the selected website field.";
          }else{
            selected="none";
            fieldStatus.textContent="Text was NOT entered. Tap a website input first; your text is preserved.";
          }
          pendingText=null;updateTypingEnabled();
        }
        if(m.type==="frame"){
          if(!ready){
            ready=true;
            status.textContent="Browser ready. Tap a website input inside the picture.";
            updateTypingEnabled();
          }
          const seq=++frameNumber,img=new Image();
          img.onload=()=>{if(seq===frameNumber)ctx.drawImage(img,0,0,1024,720);};
          img.src="data:image/jpeg;base64,"+m.image;
        }
      };
    };
    function selectInBrowser(e){
      if(!ready){
        fieldStatus.textContent="Browser preview is not connected. Open secure browser before tapping its fields.";
        return;
      }
      const r=canvas.getBoundingClientRect();
      if(!r.width||!r.height)return;
      const x=Math.max(0,Math.min(1023,Math.floor((e.clientX-r.left)*1024/r.width))),
        y=Math.max(0,Math.min(719,Math.floor((e.clientY-r.top)*720/r.height)));
      if(send({type:"click",x:x,y:y})){
        selected="none";updateTypingEnabled();
        fieldStatus.textContent="Selecting website field...";
      }
    }
    // Pointer-up supports touch selection in iPad browsers. Ignore its
    // subsequent synthetic click to avoid accidentally submitting twice.
    canvas.addEventListener("pointerup",e=>{
      if(e.pointerType==="touch"){
        e.preventDefault();lastTouchAt=Date.now();selectInBrowser(e);
      }
    });
    canvas.onclick=e=>{
      if(Date.now()-lastTouchAt>800)selectInBrowser(e);
    };
    typeButton.onclick=()=>{
      if(pendingText!==null||selected==="none"||!textInput.value){
        fieldStatus.textContent="Select a website field and enter text before typing.";
        return;
      }
      const value=textInput.value;
      if(send({type:"type",value:value})){
        pendingText=value;updateTypingEnabled();
        fieldStatus.textContent="Sending to selected field. Waiting for browser confirmation...";
      }
    };
    document.getElementById("enter").onclick=()=>send({type:"key",key:"Enter"});
    document.getElementById("tab").onclick=()=>send({type:"key",key:"Tab"});
    document.getElementById("reload").onclick=()=>send({type:"reload"});
    document.getElementById("save").onclick=()=>{
      if(saveInFlight||!ready)return;
      if(send({type:"save"})){
        saveInFlight=true;updateTypingEnabled();
        status.textContent="Saving encrypted website session...";
      }
    };
    document.getElementById("close").onclick=()=>{send({type:"close"});if(ws)ws.close()};
    </script></body></html>""".replace("__NONCE__",nonce)


async def _frame(ws,page):
    jpeg=await page.screenshot(type="jpeg",quality=55,timeout=12000)
    await ws.send_json({"type":"frame","image":base64.b64encode(jpeg).decode("ascii")})


def mount_private_login(app):
    @app.get("/owner/sign-in",response_class=HTMLResponse)
    async def sign_in(_owner=Depends(require_verified_owner)):
        nonce=secrets.token_urlsafe(20)
        return HTMLResponse(login_html(nonce),
            headers={
                "Cache-Control":"no-store",
                "X-Content-Type-Options":"nosniff",
                "Referrer-Policy":"no-referrer",
                "Content-Security-Policy":
                    "default-src 'none'; style-src 'unsafe-inline'; "
                    f"script-src 'nonce-{nonce}'; "
                    "connect-src 'self' wss:; img-src data:; "
                    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
            })

    @app.websocket("/owner/live")
    async def live(ws:WebSocket,site:str,demo:str="0"):
        # IAP's unsigned email headers can be forged; accept only its signed JWT.
        try:
            # Auth0 portal accepts only Authlib-verified and signed owner
            # session. The original Google IAP service still requires ES256.
            owner = (auth0_verified_session(ws.scope) if auth0_active()
                     else verify_owner_token(
                         ws.headers.get("x-goog-iap-jwt-assertion","")))
            expected=os.environ.get("BROWSER_PUBLIC_ORIGIN","")
            ci=(os.environ.get("COMPUTER_BROWSER_CI_ONLY","")=="true")
            if (not expected or ws.headers.get("origin")!=expected or
                    (not expected.startswith("https://") and not ci)):
                raise PermissionError("Origin not owner authorized")
            if not safe_url(site):
                raise PermissionError("Website is not on owner's allowed origins")
            if demo=="1" and not ci:
                raise PermissionError("Offline demonstration is not enabled")
            if demo not in ("0","1"):
                raise PermissionError("Unknown execution mode")
            await ws.accept()
        except PermissionError:
            await ws.close(code=4403)
            return

        browser=None
        phase="destination_check"
        from playwright.async_api import async_playwright
        try:
            await ws.send_json({"type":"status","message":"Opening private browser"})
            if demo=="0":
                await asyncio.to_thread(public_dns_only,site)
            phase="chromium_start"
            async with async_playwright() as playwright:
                browser=await playwright.chromium.launch(headless=True)
                context=await browser.new_context(
                    viewport={"width":1024,"height":720},accept_downloads=False,
                    service_workers="block",ignore_https_errors=False,
                    permissions=[])
                if demo=="0":
                    async def limited_origin(route):
                        req=route.request
                        if (req.method in {"GET","HEAD","POST","OPTIONS"} and
                                safe_url(req.url)):
                            await route.continue_()
                        else:
                            await route.abort()
                    await context.route("**/*",limited_origin)
                else:
                    await context.route("**/*",lambda route:route.abort())
                page=await context.new_page()
                phase="website_load"
                if demo=="1":
                    await page.set_content("""<html><body>
                        <input id="entry" aria-label="Local field">
                        <button id="preview" onclick="document.getElementById('out').innerText=
                        document.getElementById('entry').value">Preview locally</button>
                        <p id="out">None</p></body></html>""")
                else:
                    await page.goto(site,wait_until="domcontentloaded",timeout=25000)
                phase="live_interaction"
                await _frame(ws,page)
                for number in range(160):
                    command=await ws.receive_json()
                    if not isinstance(command,dict) or len(str(command))>5000:
                        raise PermissionError("Oversized browser command")
                    kind=command.get("type")
                    if kind=="click":
                        x,y=command.get("x"),command.get("y")
                        if (not isinstance(x,int) or not isinstance(y,int) or
                                not 0<=x<1024 or not 0<=y<720):
                            raise PermissionError("Click coordinates outside visible browser")
                        await page.mouse.click(x,y)
                        await ws.send_json({"type":"ack","action":"click",
                                            "field":await _focused_editable_kind(page)})
                    elif kind=="type":
                        text=command.get("value","")
                        if not isinstance(text,str) or len(text)>2000:
                            raise PermissionError("Invalid typed input")
                        field=await _focused_editable_kind(page)
                        if field=="none":
                            await ws.send_json({"type":"ack","action":"type","ok":False})
                            continue
                        await page.keyboard.insert_text(text)
                        await ws.send_json({"type":"ack","action":"type","ok":True})
                    elif kind=="key":
                        if command.get("key") not in {"Enter","Tab","Backspace"}:
                            raise PermissionError("Unsupported key combination")
                        await page.keyboard.press(command["key"])
                    elif kind=="reload":
                        if demo=="0":
                            await page.reload(wait_until="domcontentloaded",timeout=25000)
                    elif kind=="save":
                        if demo=="1":
                            await ws.send_json({"type":"save_result","ok":False,
                                "message":"Offline test does not save login state"})
                            continue
                        try:
                            origin="https://"+urlsplit(site).hostname
                            # Official Playwright supports IndexedDB auth state
                            # (e.g. Firebase); default storage_state() omits it.
                            # The origin filter below keeps only THIS website.
                            # We intentionally exclude virtual WebAuthn private keys
                            # and OPFS data by not requesting those options.
                            storage=filter_site_storage(
                                await context.storage_state(indexed_db=True), origin
                            )
                            if not storage["cookies"] and not storage["origins"]:
                                await ws.send_json({"type":"save_result","ok":False,
                                    "message":"No website session data to save. Browser remains open."})
                                continue
                            await asyncio.to_thread(_persist_encrypted_site_profile,
                                owner_id=owner["private_owner_id"],
                                origin=origin,state=storage)
                        except Exception:
                            # Storage errors are not browser failures: never
                            # reveal GCS metadata, tokens, cookies or key values.
                            # Keep the original authenticated Chromium live.
                            await ws.send_json({"type":"save_result","ok":False,
                                "message":"Encrypted session storage unavailable. Browser remains open; saving was not confirmed."})
                            continue
                        await ws.send_json({"type":"save_result","ok":True,
                            "message":"Website state stored encrypted; website login restoration not yet verified"})
                        continue
                    elif kind=="close":
                        break
                    else:
                        raise PermissionError("Unknown browser operation")
                    if demo=="0" and not safe_url(page.url):
                        raise PermissionError("Website redirected off authorized origins")
                    await _frame(ws,page)
                else:
                    await ws.send_json({"type":"status","failure":True,
                                        "message":"Browser action limit reached; reopen a fresh browser."})
        except WebSocketDisconnect:
            pass
        except Exception:
            # Only fixed, non-sensitive phases are shown. Never expose website
            # URLs, remote page content, cookies, Cloud Run internals or tokens.
            failures={
                "destination_check":"Website destination could not pass DNS safety checks.",
                "chromium_start":"Private Chromium could not start on the browser server.",
                "website_load":"Approved website did not load in private Chromium.",
                "live_interaction":"Private browser interaction ended unexpectedly.",
            }
            try:
                await ws.send_json({"type":"status","failure":True,
                    "message":failures.get(phase,"Private browser operation failed.")})
            except Exception:
                pass
        finally:
            if browser is not None:
                await browser.close()
            try:
                await ws.close()
            except Exception:
                pass
