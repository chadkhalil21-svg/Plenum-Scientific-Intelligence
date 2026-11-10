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

from fastapi import Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from .engine import safe_url, public_dns_only
from .iap_identity import verify_owner_token
from .owner_auth0 import active as auth0_active, verified_session as auth0_verified_session
from .owner_console import require_verified_owner
from .private_profiles import BrowserProfileStore
from .owner_live_access import owner_live_origin


# Apple documents these exact HTTPS hosts as Apple Account sign-in dependencies.
# An owner must opt in for EACH private App Store Connect session. The existing
# public-IP pinned proxy still rejects every unlisted destination, and other
# registered websites retain their original exact single-origin policy.
_APP_STORE_ORIGIN = "https://appstoreconnect.apple.com"
_APPLE_LOGIN_ORIGINS = frozenset({
    "https://idmsa.apple.com",
    "https://appleid.cdn-apple.com",
    "https://account.apple.com",
    "https://gsa.apple.com",
})


def _approved_live_origins(origin, *, dynamic, apple_auth):
    if apple_auth not in ("0", "1"):
        raise PermissionError("Invalid Apple authentication permission")
    if apple_auth == "0":
        return frozenset({origin})
    if origin != _APP_STORE_ORIGIN or not dynamic:
        raise PermissionError("Apple sign-in scope requires registered private site")
    return frozenset({origin}) | _APPLE_LOGIN_ORIGINS


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
    <p>For a new website, first register its exact HTTPS origin through
    <a href="/owner/sites">Manage registered websites</a>. Only the verified
    owner may activate its private sign-in; traffic is limited to that site.
    Cross-site Google/Apple identity redirects can still be blocked.</p>
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
    <label><input id="apple-auth" type="checkbox">
    For App Store Connect only: permit Apple's four documented sign-in hosts
    during this private browser session. All other websites remain blocked.
    Sign-in and MFA remain thine own actions.</label>
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
    let pageBlank=true;
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
      document.getElementById("save").disabled=!ready||saveInFlight||pageBlank;
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
    document.getElementById("open").onclick=async()=>{
      if(ws)ws.close();
      ws=null;ready=false;pageBlank=true;selected="none";pendingText=null;saveInFlight=false;
      updateTypingEnabled();clearStalePreview();
      const target=document.getElementById("url").value.trim();
      const appleAuth=document.getElementById("apple-auth").checked?"1":"0";
      status.textContent="Checking owner-approved website access...";
      let access;
      try{
        access=await fetch("/owner/live-access?site="+encodeURIComponent(target)+
            "&apple_auth="+appleAuth,{
          credentials:"same-origin",cache:"no-store",headers:{"Accept":"application/json"}
        });
      }catch(_){
        status.textContent="Website access check failed. Browser not opened; check owner portal connectivity.";
        return;
      }
      if(!access.ok){
        status.textContent=access.status===401
          ?"Owner sign-in expired. Sign into the owner portal in this same Edge tab."
          :access.status===403
          ?"Website not yet authorized for private sign-in. First register its exact HTTPS origin under Manage registered websites."
          :"Website access preflight unavailable. Browser was not opened.";
        return;
      }
      const u=new URL("/owner/live",location.origin);
      u.protocol=location.protocol==="https:"?"wss:":"ws:";
      u.searchParams.set("site",target);
      u.searchParams.set("apple_auth",appleAuth);
      const connection=new WebSocket(u);
      ws=connection;ready=false;pageBlank=true;selected="none";pendingText=null;saveInFlight=false;
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
        ready=false;pageBlank=true;selected="none";pendingText=null;saveInFlight=false;updateTypingEnabled();
        clearStalePreview();
        const elapsed=openedAt===null?"":", after "+Math.round((Date.now()-openedAt)/1000)+" seconds";
        if(!serverStopped){
          if(e.code===4403||(!connected&&e.code===1006))
            status.textContent="Browser WebSocket upgrade did not complete (code "+e.code+"). Website access was prechecked; connection or owner session must be diagnosed.";
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
            serverStopped=true;ready=false;pageBlank=true;selected="none";saveInFlight=false;updateTypingEnabled();
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
        if(m.type==="page_health"){
          pageBlank=m.blank===true||m.render_unverified===true;
          if(m.render_unverified===true){
            status.textContent="Browser connected, but website rendering could not be verified. "+
              "Login is not confirmed; do not save this session.";
          }else if(pageBlank&&m.blocked_cross_origin>0){
            status.textContent="Browser connected, but website appears blank. "+
              "Some cross-origin resources were blocked by Plenum's current single-site "+
              "security policy. No login is confirmed; do not save this session.";
          }else if(pageBlank){
            status.textContent="Browser connected, but the website appears blank. "+
              "The cause is not established; no login is confirmed.";
          }else{
            status.textContent=m.blocked_cross_origin>0
              ?"Website picture loaded, but some cross-origin resources were blocked. "+
               "Login functionality may be incomplete."
              :"Website picture loaded. Browser connection working; login is not yet verified.";
          }
          updateTypingEnabled();
        }
        if(m.type==="frame"){
          if(!ready){
            ready=true;
            status.textContent="Browser stream connected; checking website rendering...";
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


async def _page_render_health(ws, page, blocked):
    """Redacted diagnostic, not evidence of account authentication.

    No URLs, HTML, text, login values, headers, cookies, JS stacktraces or
    selectors leave the owner-only Chromium process.
    """
    try:
        visible = await page.evaluate("""() => {
          const b=document.body;
          if (!b) return false;
          const t=(b.innerText||"").trim();
          const controls=[...b.querySelectorAll("input,button,textarea,select,a,[role=button]")]
            .some(el => {
              const r=el.getBoundingClientRect();
              const s=getComputedStyle(el);
              return r.width>0 && r.height>0 && s.display!=="none" &&
                     s.visibility!=="hidden";
            });
          return t.length > 0 || controls;
        }""")
        blank = not bool(visible)
    except Exception:
        # Evaluation errors must not be misrepresented as a blank page.
        await ws.send_json({"type":"page_health","blank":False,
                            "render_unverified":True,
                            "blocked_cross_origin":min(99,blocked["cross_origin"])})
        return
    await ws.send_json({"type":"page_health","blank":blank,
                        "blocked_cross_origin":min(99,blocked["cross_origin"])})


def mount_private_login(app):
    @app.get("/owner/live-access")
    async def live_access(site: str=Query(min_length=9,max_length=1200),
                          apple_auth: str="0",
                          _owner=Depends(require_verified_owner)):
        """Same-origin, verified-owner HTTP preflight; no browser or secrets."""
        try:
            origin, pinned=owner_live_origin(
                owner_id=_owner["private_owner_id"],site=site)
            approved_origins=_approved_live_origins(
                origin,dynamic=pinned,apple_auth=apple_auth)
        except PermissionError as exc:
            raise HTTPException(status_code=403,
                                detail="Website not approved for private sign-in") from exc
        return {"approved":True,"pinned_single_origin":pinned and apple_auth=="0",
                "pinned_exact_origins":len(approved_origins) if pinned else 0,
                "site_specific_owner_consent":True,
                "login_restoration_verified":False}

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
    async def live(ws:WebSocket,site:str,demo:str="0",apple_auth:str="0"):
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
            origin, dynamic=owner_live_origin(
                owner_id=owner["private_owner_id"],site=site)
            approved_origins=_approved_live_origins(
                origin,dynamic=dynamic,apple_auth=apple_auth)
            if demo=="1" and (not ci or apple_auth=="1"):
                raise PermissionError("Offline demonstration is not enabled")
            if demo not in ("0","1"):
                raise PermissionError("Unknown execution mode")
            await ws.accept()
        except PermissionError:
            await ws.close(code=4403)
            return

        browser=None
        broker=None
        refresh_task=None
        phase="destination_check"
        from playwright.async_api import async_playwright
        try:
            await ws.send_json({"type":"status","message":"Opening private browser"})
            if demo=="0":
                await asyncio.to_thread(public_dns_only,site)
            if dynamic and demo=="0":
                from .pinned_public_preview import PinnedOriginProxy
                # Reuse exact public-IP-pinned CONNECT proxy already audited
                # for registered website previews. No direct cross-site egress.
                broker=PinnedOriginProxy(
                    origin,additional_origins=approved_origins-{origin},
                    max_tunnels=16,
                    max_tunnel_bytes=30_000_000,max_lifetime=600)
                await broker.__aenter__()
            phase="chromium_start"
            async with async_playwright() as playwright:
                launch={"headless":True}
                if broker is not None:
                    launch.update({
                        "proxy":{"server":f"http://127.0.0.1:{broker.port}"},
                        "args":["--disable-background-networking",
                                "--disable-quic",
                                "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                    })
                browser=await playwright.chromium.launch(**launch)
                context=await browser.new_context(
                    viewport={"width":1024,"height":720},accept_downloads=False,
                    service_workers="block",ignore_https_errors=False,
                    permissions=[])
                blocked={"cross_origin":0}
                if demo=="0":
                    async def limited_origin(route):
                        req=route.request
                        if (req.method in {"GET","HEAD","POST","OPTIONS"} and
                                safe_url(req.url,origins=approved_origins)):
                            await route.continue_()
                        else:
                            if not safe_url(req.url,origins=approved_origins):
                                blocked["cross_origin"]+=1
                            await route.abort()
                    await context.route("**/*",limited_origin)
                    if dynamic:
                        # Browser request interception does not automatically
                        # cover WebSocket frames. Block website-created
                        # sockets until a separate reviewed socket policy exists.
                        await context.route_web_socket(
                            "**/*",lambda route:route.close())
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
                # The first screenshot can precede JavaScript's first paint.
                # Repaint the SAME owner-only Chromium without needing a click.
                # Cap the stream, and serialize it with action screenshots.
                frame_lock=asyncio.Lock()
                async def show_picture():
                    async with frame_lock:
                        await _frame(ws,page)
                        await _page_render_health(ws,page,blocked)

                await show_picture()

                if demo=="0":
                    async def refresh_picture():
                        for tick in range(200):
                            await asyncio.sleep(3)
                            if dynamic and tick % 10 == 9:
                                # Recheck revoked grants without placing the
                                # synchronous GCS request on the event loop.
                                try:
                                    owner_origin, pinned=await asyncio.to_thread(
                                        owner_live_origin,
                                        owner_id=owner["private_owner_id"],site=site)
                                    if owner_origin!=origin or not pinned:
                                        raise PermissionError("Owner grant revoked")
                                except Exception:
                                    # An unavailable/revoked registration cannot
                                    # keep an owner stream alive indefinitely.
                                    await ws.close(code=4403)
                                    return
                            try:
                                await show_picture()
                            except asyncio.CancelledError:
                                raise
                            except Exception:
                                return  # A failed repaint does not imply login.

                    refresh_task=asyncio.create_task(refresh_picture())

                for number in range(160):
                    command=await ws.receive_json()
                    if dynamic:
                        # Revoked/expired registration must stop future owner
                        # commands, including saving credentials.
                        check_origin, check_pinned=owner_live_origin(
                            owner_id=owner["private_owner_id"],site=site)
                        if check_origin!=origin or not check_pinned:
                            raise PermissionError("Owner site grant expired or revoked")
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
                        if not safe_url(page.url,origins={origin}):
                            await ws.send_json({"type":"save_result","ok":False,
                                "message":"Return to the original website before saving its session."})
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
                    if demo=="0" and not safe_url(page.url,origins=approved_origins):
                        raise PermissionError("Website redirected off authorized origins")
                    await show_picture()
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
            if refresh_task is not None:
                refresh_task.cancel()
                try:
                    await refresh_task
                except asyncio.CancelledError:
                    pass
            if browser is not None:
                await browser.close()
            if broker is not None:
                try:
                    await broker.__aexit__(None,None,None)
                except Exception:
                    pass
            try:
                await ws.close()
            except Exception:
                pass
