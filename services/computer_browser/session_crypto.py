"""Encrypted, owner/site-bound browser state envelope.

This only tests preservation of synthetic cookies. It is not yet a persistent
GCS/KMS vault or authenticated website login. NEVER return sealed state to
ChatGPT, Github issues or model-visible tools.
"""
import json
import time
from urllib.parse import urlsplit

MAX_STATE_BYTES = 160_000
MAX_TTL_SECONDS = 86400


class PrivateSessionVault:
    def __init__(self, fernet_key: bytes):
        from cryptography.fernet import Fernet
        self._fernet = Fernet(fernet_key)

    def encrypt(self, state, owner, site_origin, ttl_seconds=3600, now=None):
        if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
            raise ValueError("Expected genuine Playwright storage state mapping")
        if not isinstance(owner, str) or not 1 <= len(owner) <= 80 or "/" in owner:
            raise ValueError("Invalid tenant label")
        parsed = urlsplit(site_origin)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.path or parsed.query or parsed.fragment or parsed.username):
            raise ValueError("Expected bare HTTPS site origin")
        if not 1 <= ttl_seconds <= MAX_TTL_SECONDS:
            raise ValueError("Session lifespan exceeds bound")
        issued = int(time.time() if now is None else now)
        data = json.dumps({
            "schema":"plenum-session-envelope-v1",
            "owner":owner,
            "site":site_origin,
            "created":issued,
            "expires":issued + ttl_seconds,
            "storage_state":state,
        },separators=(",",":"),ensure_ascii=False).encode()
        if len(data) > MAX_STATE_BYTES:
            raise ValueError("Browser session too large")
        return self._fernet.encrypt(data)

    def decrypt(self, ciphertext, owner, site_origin, now=None):
        from cryptography.fernet import InvalidToken
        if not isinstance(ciphertext,bytes) or len(ciphertext)>MAX_STATE_BYTES*2:
            raise PermissionError("Malformed session envelope")
        try:
            data=json.loads(self._fernet.decrypt(ciphertext))
        except (InvalidToken, ValueError, TypeError) as exc:
            raise PermissionError("Session decryption failed") from exc
        t=int(time.time() if now is None else now)
        if (data.get("schema")!="plenum-session-envelope-v1" or
                data.get("owner") != owner or data.get("site") != site_origin or
                t < data.get("created",-1) or t >= data.get("expires",-1)):
            raise PermissionError("Wrong owner, site or expired session")
        state=data.get("storage_state")
        if not isinstance(state,dict) or not isinstance(state.get("cookies"),list):
            raise PermissionError("Invalid restored browser context")
        return state


async def local_encrypted_context_roundtrip():
    """Real Chromium with artificial cookie, no outbound requests or login."""
    from cryptography.fernet import Fernet
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            a=await browser.new_context(accept_downloads=False)
            await a.add_cookies([{
                "name":"test-only", "value":"synthetic-not-a-credential",
                "domain":"example.com", "path":"/",
                "httpOnly":True, "secure":True, "sameSite":"Lax",
            }])
            state=await a.storage_state()
            key=Fernet.generate_key()
            vault=PrivateSessionVault(key)
            ciphertext=vault.encrypt(state,"computer","https://example.com",ttl_seconds=60)
            if b"synthetic-not-a-credential" in ciphertext:
                raise AssertionError("Encrypted bytes leaked plaintext synthetic cookie")
            restored=vault.decrypt(ciphertext,"computer","https://example.com")
            b=await browser.new_context(storage_state=restored,accept_downloads=False)
            try:
                cookies=await b.cookies("https://example.com/")
                if not any(c["name"]=="test-only" and
                           c["value"]=="synthetic-not-a-credential" for c in cookies):
                    raise AssertionError("Actual Playwright session restore failed")
            finally:
                await b.close()
            await a.close()
            return {
                "schema":"plenum-local-encrypted-browser-context-v1",
                "actual_chromium_state_restored":True,
                "encrypted_state_exposed_to_user":False,
                "only_synthetic_credentials_used":True,
                "external_website_login_verified":False,
                "private_cloud_storage_connected":False,
                "AGI_demonstrated":False,
            }
        finally:
            await browser.close()
