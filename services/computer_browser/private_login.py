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
    """Save only target-site cookies and local storage, never IdP credentials."""
    h=urlsplit(site_origin).hostname
    if not h:
        raise ValueError("Missing site origin")
    def same_site(cookie):
        d=str(cookie.get("domain","")).lower().lstrip(".")
        return d==h or h.endswith("."+d)
    return {
        "cookies":[c for c in state.get("cookies",[]) if same_site(c)],
        "origins":[o for o in state.get("origins",[])
                   if urlsplit(o.get("origin","")).hostname==h]
    }


def login_html(nonce):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Computer · Secure Website Login</title>
    <style>body{font:16px system-ui;margin:16px auto;padding:0 12px;max-width:1060px}
    button,input{font:inherit;padding:9px;margin:3px}
    input#url{width:78%;max-width:720px}input#text{width:64%;max-width:680px}
    canvas{border:1px solid gray;width:100%;max-width:1024px;background:#eee}
    #status{white-space:pre-wrap}h1{font-size:23px}</style></head><body>
    <h1>Computer · Private Website Sign-in</h1>
    <p>Open an approved website. Sign in here rather than sharing passwords
    in ChatGPT. This browser runs only while the private session is connected.</p>
    <label>Website <input id="url" value="https://the-internet.herokuapp.com/login"
    maxlength="1200" autocomplete="off"></label>
    <button id="open">Open secure browser</button>
    <p id="status" role="status">Not connected</p>
    <canvas width="1024" height="720" id="display" aria-label="Remote Chromium view"></canvas>
    <p><input type="password" id="text" autocomplete="off"
    placeholder="Type privately into selected website field">
    <button id="type">Type</button>
    <button id="enter">Enter</button>
    <button id="tab">Tab</button>
    <button id="reload">Reload</button>
    <button id="save">Save this website login</button>
    <button id="close">Close</button></p>
    <script nonce="__NONCE__">
    let ws=null;const canvas=document.getElementById("display"),
    ctx=canvas.getContext("2d"),status=document.getElementById("status");
    function send(m){if(ws&&ws.readyState===1)ws.send(JSON.stringify(m));
      else status.textContent="Open a website first."}
    document.getElementById("open").onclick=()=>{
      if(ws)ws.close();const u=new URL("/owner/live",location.origin);
      u.protocol=location.protocol==="https:"?"wss:":"ws:";
      u.searchParams.set("site",document.getElementById("url").value.trim());
      ws=new WebSocket(u);
      ws.onopen=()=>status.textContent="Browser connected.";
      ws.onclose=()=>status.textContent="Private browser closed.";
      ws.onerror=()=>status.textContent="Browser unavailable or unauthorized.";
      ws.onmessage=e=>{const m=JSON.parse(e.data);
        if(m.type==="status")status.textContent=m.message;
        if(m.type==="frame"){const img=new Image();
          img.onload=()=>ctx.drawImage(img,0,0,1024,720);
          img.src="data:image/jpeg;base64,"+m.image;}
      };
    };
    canvas.onclick=e=>{let r=canvas.getBoundingClientRect();
      send({type:"click",x:Math.floor((e.clientX-r.left)*1024/r.width),
        y:Math.floor((e.clientY-r.top)*720/r.height)})};
    document.getElementById("type").onclick=()=>{
      const inp=document.getElementById("text");
      send({type:"type",value:inp.value});inp.value="";};
    document.getElementById("enter").onclick=()=>send({type:"key",key:"Enter"});
    document.getElementById("tab").onclick=()=>send({type:"key",key:"Tab"});
    document.getElementById("reload").onclick=()=>send({type:"reload"});
    document.getElementById("save").onclick=()=>send({type:"save"});
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
        from playwright.async_api import async_playwright
        try:
            await ws.send_json({"type":"status","message":"Opening private browser"})
            if demo=="0":
                await asyncio.to_thread(public_dns_only,site)
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
                if demo=="1":
                    await page.set_content("""<html><body>
                        <input id="entry" aria-label="Local field">
                        <button id="preview" onclick="document.getElementById('out').innerText=
                        document.getElementById('entry').value">Preview locally</button>
                        <p id="out">None</p></body></html>""")
                else:
                    await page.goto(site,wait_until="domcontentloaded",timeout=25000)
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
                    elif kind=="type":
                        text=command.get("value","")
                        if not isinstance(text,str) or len(text)>2000:
                            raise PermissionError("Invalid typed input")
                        await page.keyboard.insert_text(text)
                    elif kind=="key":
                        if command.get("key") not in {"Enter","Tab","Backspace"}:
                            raise PermissionError("Unsupported key combination")
                        await page.keyboard.press(command["key"])
                    elif kind=="reload":
                        if demo=="0":
                            await page.reload(wait_until="domcontentloaded",timeout=25000)
                    elif kind=="save":
                        if demo=="1":
                            await ws.send_json({"type":"status","message":"Offline test does not save login state"})
                            continue
                        origin="https://"+urlsplit(site).hostname
                        storage=filter_site_storage(await context.storage_state(),origin)
                        if not storage["cookies"] and not storage["origins"]:
                            await ws.send_json({"type":"status","message":"No website session to save"})
                            continue
                        store=BrowserProfileStore.from_environment()
                        generation=store.current_generation(owner=owner["private_owner_id"],origin=origin)
                        if generation is None:
                            store.save_new(owner=owner["private_owner_id"],origin=origin,
                                state=storage,ttl_seconds=86400)
                        else:
                            store.replace_if_current(owner=owner["private_owner_id"],origin=origin,
                                state=storage,expected_generation=generation,ttl_seconds=86400)
                        await ws.send_json({"type":"status",
                            "message":"Website login saved privately in encrypted storage"})
                        continue
                    elif kind=="close":
                        break
                    else:
                        raise PermissionError("Unknown browser operation")
                    if demo=="0" and not safe_url(page.url):
                        raise PermissionError("Website redirected off authorized origins")
                    await _frame(ws,page)
        except WebSocketDisconnect:
            pass
        except Exception:
            try:
                await ws.send_json({"type":"status",
                    "message":"Browser session stopped; check site permissions or cloud setup"})
            except Exception:
                pass
        finally:
            if browser is not None:
                await browser.close()
            try:
                await ws.close()
            except Exception:
                pass
