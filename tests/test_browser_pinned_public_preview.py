"""Original per-owner registered-site Chromium egress boundary tests.

No credentials or account data. Tests fail closed on private addresses,
cross-site CONNECT requests, forged owner approval and disabled feature.
Only public example.com may be used by the optional new proxy integration.
"""
import asyncio
import importlib.util
import os
import socket
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

FASTAPI = importlib.util.find_spec("fastapi") is not None
CRYPTO = importlib.util.find_spec("cryptography") is not None
PLAYWRIGHT = importlib.util.find_spec("playwright") is not None

if FASTAPI and CRYPTO:
    from services.computer_browser import pinned_public_preview as preview
    from services.computer_browser import runtime_site_grants as grants
    from services.computer_browser.owner_saved_session import _owner_form_token
    from services.computer_browser.owner_console import require_verified_owner
else:
    preview = None
    grants = None

OWNER = "a" * 64
SITE = "https://example.org"
ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_RUNTIME_SITE_GRANTS_ENABLED": "true",
    "PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED": "true",
    "BROWSER_ALLOWED_ORIGINS": "https://example.com",
    "BROWSER_PUBLIC_ORIGIN": "https://computer.example.com",
    "COMPUTER_BROWSER_TOKEN": "private-runtime-site-csrf-" * 3,
}


@unittest.skipUnless(FASTAPI and CRYPTO, "Optional browser gateway packages absent")
class PinnedNetworkPolicyTests(unittest.TestCase):
    def _dns(self, ip):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                 "", (ip, 443))]

    def test_all_public_only_and_fixed_ip_no_rebinding(self):
        with patch.object(preview.socket, "getaddrinfo",
                          return_value=self._dns("93.184.215.14")) as resolver:
            self.assertEqual(preview.resolve_public_ip(SITE), "93.184.215.14")
            self.assertEqual(resolver.call_count, 1)
        for ip in ("127.0.0.1", "169.254.169.254",
                   "10.0.0.1", "172.17.0.1", "192.168.1.1",
                   "0.0.0.0", "100.64.0.1", "192.0.2.1"):
            with self.subTest(ip=ip),patch.object(preview.socket,"getaddrinfo",
                                                 return_value=self._dns(ip)):
                with self.assertRaises(PermissionError):
                    preview.resolve_public_ip(SITE)
        with patch.object(preview.socket, "getaddrinfo",
                          return_value=self._dns("93.184.215.14") +
                                       self._dns("127.0.0.1")):
            with self.assertRaises(PermissionError):
                preview.resolve_public_ip(SITE)

    def test_only_canonical_owner_sites_accepted(self):
        for bad in ("https://127.0.0.1", "http://example.org",
                    "https://example.org/login",
                    "https://example.org@169.254.169.254",
                    "https://example.org:8080", "https://internal.local"):
            with self.subTest(site=bad),self.assertRaises(PermissionError):
                preview.resolve_public_ip(bad)

    def test_disabled_read_and_missing_owner_grant_fail_before_network(self):
        async def run():
            with patch.dict(os.environ, ENV):
                with patch.object(preview.OwnerSiteGrantStore,
                                  "from_environment") as storage, \
                     patch.object(preview, "PinnedOriginProxy") as proxy:
                    fake = MagicMock()
                    fake.authorized.return_value = False
                    storage.return_value = fake
                    with self.assertRaises(PermissionError):
                        await preview.read_registered_public(
                            owner=OWNER,site=SITE,path="/about")
                    proxy.assert_not_called()
                    fake.authorized.assert_called_once_with(owner=OWNER,origin=SITE)
                    with patch.dict(os.environ,
                                    {"PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED":"false"}):
                        with self.assertRaises(PermissionError):
                            await preview.read_registered_public(
                                owner=OWNER,site=SITE,path="/")
        asyncio.run(run())


@unittest.skipUnless(FASTAPI and CRYPTO, "Optional browser gateway packages absent")
class PinnedProxyOriginalSocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_reject_unregistered_tunnel_and_non_connect_method(self):
        with patch.object(preview, "resolve_public_ip",
                          return_value="93.184.215.14"):
            async with preview.PinnedOriginProxy(SITE) as proxy:
                for first in (
                    b"CONNECT 169.254.169.254:443 HTTP/1.1",
                    b"CONNECT attacker.example:443 HTTP/1.1",
                    b"CONNECT example.org:8080 HTTP/1.1",
                    b"GET https://example.org/ HTTP/1.1",
                ):
                    reader, writer = await asyncio.open_connection(
                        "127.0.0.1", proxy.port)
                    writer.write(first+b"\r\nHost: example.org\r\n\r\n")
                    await writer.drain()
                    response = await asyncio.wait_for(reader.read(200),timeout=3)
                    self.assertIn(b"403 Forbidden",response)
                    writer.close()
                    await writer.wait_closed()
                self.assertEqual(proxy.accepted,0)

    async def test_valid_tunnel_uses_only_prevalidated_literal_public_ip(self):
        async def local_echo(reader, writer):
            data = await reader.read(64)
            writer.write(data.upper())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        echo = await asyncio.start_server(local_echo,"127.0.0.1",0)
        echo_port=echo.sockets[0].getsockname()[1]
        original_connect=asyncio.open_connection
        remote_attempts=[]
        async def proxy_socket(host,port,*args,**kwargs):
            if host=="93.184.215.14" and port==443:
                remote_attempts.append((host,port))
                # Offline mock for a safe IP literal. No real Internet access.
                return await original_connect("127.0.0.1",echo_port)
            return await original_connect(host,port,*args,**kwargs)
        try:
            with patch.object(preview, "resolve_public_ip",
                              return_value="93.184.215.14"):
                async with preview.PinnedOriginProxy(SITE) as proxy:
                    with patch.object(preview.asyncio,"open_connection",
                                      side_effect=proxy_socket):
                        reader,writer=await original_connect("127.0.0.1",proxy.port)
                        writer.write(b"CONNECT example.org:443 HTTP/1.1\r\n"
                                     b"Host: example.org:443\r\n\r\n")
                        await writer.drain()
                        response=await reader.readuntil(b"\r\n\r\n")
                        self.assertIn(b"200 Connection Established",response)
                        writer.write(b"synthetic")
                        await writer.drain()
                        echo_data=await asyncio.wait_for(reader.read(32),timeout=3)
                        self.assertEqual(echo_data,b"SYNTHETIC")
                        writer.close()
                        await writer.wait_closed()
                    self.assertEqual(proxy.accepted,1)
                    self.assertEqual(remote_attempts,[("93.184.215.14",443)])
        finally:
            echo.close()
            await echo.wait_closed()


@unittest.skipUnless(FASTAPI and CRYPTO, "Optional browser gateway packages absent")
class OwnerOnlyRegisteredPreviewTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        self.env=patch.dict(os.environ,ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app=FastAPI()
        grants.mount_runtime_site_grants(self.app)
        self.app.dependency_overrides[require_verified_owner]=lambda:{
            "private_owner_id":OWNER}
        self.client=TestClient(self.app)
        self.store=MagicMock()
        self.store.list_active.return_value=[
            {"origin":SITE,"issued":1,"expires":1_800_000_000}]
        self.store_patch=patch.object(grants.OwnerSiteGrantStore,
            "from_environment",return_value=self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)

    def _form(self,path="/research"):
        return {"site":SITE,"path":path,
                "csrf_token":_owner_form_token(OWNER,SITE,"site_preview")}

    def test_registry_uses_original_auth_owner_csrf_and_html_escaping(self):
        page=self.client.get("/owner/sites")
        self.assertEqual(page.status_code,200)
        self.assertIn("Read public page securely",page.text)
        with patch.object(preview,"read_registered_public",
                          new_callable=AsyncMock,return_value={
            "site":SITE,"final_url":SITE+"/research",
            "title":"Untrusted <img src=x onerror=alert(1)>",
            "body":"Synthetic owner data <script>alert(1)</script>",
            "http_status":200,
        }) as run:
            response=self.client.post("/owner/sites/preview",data=self._form())
        self.assertEqual(response.status_code,200)
        self.assertIn("&lt;script&gt;",response.text)
        self.assertNotIn("<script>alert",response.text)
        self.assertNotIn("<img src=x",response.text)
        self.assertEqual(response.headers.get("cache-control"),"no-store")
        run.assert_awaited_once_with(owner=OWNER,site=SITE,path="/research")

    def test_owner_wrong_action_origin_and_path_denied_before_browser(self):
        wrong=_owner_form_token(OWNER,SITE,"site_revoke")
        tests=[
            ({**self._form(),"csrf_token":wrong},{}),
            ({**self._form(),"csrf_token":""},{}),
            (self._form("https://evil.example/"),{}),
            (self._form("//169.254.169.254"),{}),
            (self._form("/a#fragment"),{}),
            (self._form(),{"origin":"https://foreign.example.com"}),
            (self._form(),{"sec-fetch-site":"cross-site"}),
        ]
        with patch.object(preview,"read_registered_public",
                          new_callable=AsyncMock) as run:
            for payload,headers in tests:
                with self.subTest(payload=payload,headers=headers):
                    result=self.client.post("/owner/sites/preview",
                                            data=payload,headers=headers)
                    self.assertEqual(result.status_code,403)
            run.assert_not_awaited()

    def test_preview_does_not_expose_creds_or_accept_disabled_flag(self):
        with patch.dict(os.environ,
                        {"PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED":"false"}):
            response=self.client.post("/owner/sites/preview",data=self._form())
            self.assertEqual(response.status_code,404)


@unittest.skipUnless(FASTAPI and CRYPTO and PLAYWRIGHT,
                     "Chromium proxy integration needs browser packages")
class RealPublicProxyReadTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("PLENUM_BROWSER_NEW_PROXY_LIVE_CI")=="true",
                         "Live public proxy fixture only in existing browser CI")
    def test_chromium_reaches_one_origin_through_pinned_proxy_with_no_session(self):
        async def run():
            store=MagicMock()
            store.authorized.return_value=True
            with patch.dict(os.environ,ENV),patch.object(
                    preview.OwnerSiteGrantStore,"from_environment",
                    return_value=store):
                result=await preview.read_registered_public(
                    owner=OWNER,site="https://example.com",path="/")
            self.assertEqual(result["http_status"],200)
            self.assertEqual(result["site"],"https://example.com")
            self.assertEqual(result["final_url"],"https://example.com/")
            self.assertTrue(result["pinned_public_ip_used"])
            self.assertFalse(result["website_changed"])
            self.assertFalse(result["signed_in_site_used"])
            self.assertFalse(result["javascript_executed"])
        asyncio.run(run())
