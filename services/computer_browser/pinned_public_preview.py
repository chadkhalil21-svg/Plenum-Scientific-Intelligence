"""Bounded registered-site public HTML preview via original Chromium and pinned egress.

This is NOT an authenticated browser, arbitrary network firewall, proxy service
or writable workflow. It runs in the EXISTING owner Auth0 Cloud Run process:
one verified owner, one active encrypted runtime site grant, one exact URL,
one read-only HTML document, no JavaScript, cookies, files or account writes.

All requests are forced through one ephemeral loopback HTTP CONNECT proxy
which resolves the ONLY permitted hostname once and opens TCP sockets to its
prevalidated PUBLIC IP literal. Browser HTTPS verifies the real DNS hostname.
The proxy cannot reach an IP literal, alternate host/port, internal destination
or location discovered from page content. Separate Chromium request routing
also rejects cross-origin traffic and non-GET subrequests. The two guards are
complementary: initial DNS preflight ALONE does not prevent rebinding.

This does not claim process-namespace network isolation or general interactive
website safety. Never reuse this read-only worker for signed-in accounts,
scripted third-party website actions, uploads, or form submissions.
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
from urllib.parse import urlsplit

from .engine import safe_url, excerpt
from .owner_saved_session import _approved_read_target
from .runtime_site_grants import normalize_origin, OwnerSiteGrantStore

MAX_TUNNELS = 8
MAX_TUNNEL_BYTES = 6_000_000
MAX_RESPONSE_TEXT = 1800
MAX_LIFETIME = 48


def resolve_public_ip(origin: str) -> str:
    """Select one public IP before Chromium starts; never re-resolve in tunnel."""
    origin = normalize_origin(origin)
    hostname = urlsplit(origin).hostname
    try:
        records = socket.getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise PermissionError("Registered website DNS lookup failed") from exc
    if not records or len(records) > 100:
        raise PermissionError("Unexpected registered website DNS response")
    ips = []
    for record in records:
        try:
            addr = ipaddress.ip_address(record[4][0])
        except (IndexError, ValueError) as exc:
            raise PermissionError("Invalid destination address") from exc
        if not addr.is_global:
            raise PermissionError("Website address resolves to nonpublic network")
        ips.append(addr)
    # Prefer routable IPv4 in common Cloud Run environments; otherwise IPv6.
    ips.sort(key=lambda x: (x.version != 4, x.compressed))
    return ips[0].compressed


class PinnedOriginProxy:
    """Single-origin loopback CONNECT broker, using *only* pinned public IP."""

    def __init__(self, origin: str, *, max_tunnels=MAX_TUNNELS,
                 max_tunnel_bytes=MAX_TUNNEL_BYTES, max_lifetime=MAX_LIFETIME,
                 additional_origins=()):
        """Additional exact HTTPS origins must come from a trusted owner policy.

        No suffix wildcard, browser-discovered host, URL parameter or page
        content may expand this set. Every hostname is resolved and pinned
        independently before opening Chromium.
        """
        # Defaults preserve the original public-preview security envelope.
        # Larger bounded values may be supplied only by a trusted owner worker.
        if (not all(type(v) is int for v in
                    (max_tunnels, max_tunnel_bytes, max_lifetime))
                or not 1 <= max_tunnels <= 16
                or not 1 <= max_tunnel_bytes <= 30_000_000
                or not 1 <= max_lifetime <= 600):
            raise ValueError("Invalid owner proxy transport bounds")
        self.max_tunnels = max_tunnels
        self.max_tunnel_bytes = max_tunnel_bytes
        self.max_lifetime = max_lifetime
        self.origin = normalize_origin(origin)
        self.host = urlsplit(self.origin).hostname
        if not isinstance(additional_origins, (tuple, list, frozenset, set)):
            raise ValueError("Expected explicit additional origins")
        if len(additional_origins) > 5:
            raise ValueError("Too many approved proxy origins")
        extras = frozenset(normalize_origin(item) for item in additional_origins)
        if self.origin in extras:
            raise ValueError("Duplicate primary proxy origin")
        self.additional_origins = extras
        self.host_ips = {}
        self.ip = None
        self.port = None
        self.server = None
        self.accepted = 0
        self._active = 0

    async def __aenter__(self):
        self.ip = await asyncio.to_thread(resolve_public_ip, self.origin)
        hosts = {self.host: self.ip}
        for extra in sorted(self.additional_origins):
            host = urlsplit(extra).hostname
            if host in hosts:
                raise ValueError("Duplicate approved proxy hostname")
            hosts[host] = await asyncio.to_thread(resolve_public_ip, extra)
        # Atomic publication: a failed resolution permits no tunnel.
        self.host_ips = hosts
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0,
                                                 limit=16_384)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.server.close()
        await self.server.wait_closed()

    async def _handle(self, reader, writer):
        remote = None
        if self._active >= self.max_tunnels:
            writer.close()
            await writer.wait_closed()
            return
        self._active += 1
        try:
            try:
                header = await asyncio.wait_for(
                    reader.readuntil(b"\r\n\r\n"), timeout=6)
                first = header.split(b"\r\n", 1)[0].decode("ascii")
            except (asyncio.IncompleteReadError, asyncio.LimitOverrunError,
                    asyncio.TimeoutError, UnicodeDecodeError):
                return
            # Disallow absolute-form proxy GET, alternative ports, IPv6
            # literals, CONNECT credentials, proxy auth, and proxy introspection.
            target_ip = next((
                ip for host, ip in self.host_ips.items()
                if first in (f"CONNECT {host}:443 HTTP/1.1",
                             f"CONNECT {host}:443 HTTP/1.0")
            ), None)
            if target_ip is None or b"\r\nproxy-authorization:" in header.lower():
                writer.write(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n")
                await writer.drain()
                return
            try:
                rr, rw = await asyncio.wait_for(
                    asyncio.open_connection(target_ip, 443), timeout=8)
                remote = rw
            except (OSError, asyncio.TimeoutError):
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n")
                await writer.drain()
                return
            self.accepted += 1
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            async def pump(source, destination):
                total = 0
                while True:
                    chunk = await source.read(32768)
                    if not chunk:
                        return
                    total += len(chunk)
                    if total > self.max_tunnel_bytes:
                        raise PermissionError("Public preview transfer bounded")
                    destination.write(chunk)
                    await destination.drain()
            tasks = [asyncio.create_task(pump(reader, rw)),
                     asyncio.create_task(pump(rr, writer))]
            try:
                done, pending = await asyncio.wait(
                    tasks, timeout=self.max_lifetime,
                    return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            if remote is not None:
                remote.close()
                try:
                    await remote.wait_closed()
                except OSError:
                    pass
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
            self._active -= 1


async def read_registered_public(*, owner: str, site: str, path: str):
    """One owner-approved, unauthenticated, read-only static HTML page."""
    if (os.environ.get("K_SERVICE") != "plenum-browser-owner-auth0"
            or os.environ.get("PLENUM_RUNTIME_SITE_GRANTS_ENABLED") != "true"
            or os.environ.get("PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED") != "true"):
        raise PermissionError("Registered public preview not enabled")
    site = normalize_origin(site)
    target = _approved_read_target(site, path)
    if not OwnerSiteGrantStore.from_environment().authorized(
            owner=owner, origin=site):
        raise PermissionError("Expired or revoked owner website permission")
    if not safe_url(target, origins={site}):
        raise PermissionError("Unapproved registered website target")

    from playwright.async_api import async_playwright
    async with PinnedOriginProxy(site) as broker:
        async with async_playwright() as pw:
            # This is NOT the saved-login context. We deliberately create
            # a fresh browser without storage_state or user credentials.
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-background-networking",
                      "--disable-quic",
                      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                proxy={"server": f"http://127.0.0.1:{broker.port}"})
            try:
                context = await browser.new_context(
                    service_workers="block", java_script_enabled=False,
                    accept_downloads=False, ignore_https_errors=False,
                    permissions=[], extra_http_headers={"DNT": "1"})
                try:
                    async def deny_other_requests(route):
                        req = route.request
                        if (req.method == "GET"
                                and req.resource_type == "document"
                                and safe_url(req.url, origins={site})):
                            await route.continue_()
                        else:
                            await route.abort()
                    await context.route("**/*", deny_other_requests)
                    page = await context.new_page()
                    response = await page.goto(
                        target, wait_until="domcontentloaded", timeout=20000)
                    if (response is None or response.status != 200
                            or page.url != target or broker.accepted < 1):
                        raise PermissionError(
                            "Registered site read did not reach exact approved page")
                    title = excerpt(await page.title())
                    body = " ".join(
                        (await page.locator("body").inner_text(timeout=6500)).split()
                    )[:MAX_RESPONSE_TEXT]
                    return {
                        "schema": "plenum-owner-registered-public-read-v1",
                        "site": site, "final_url": page.url,
                        "http_status": response.status,
                        "title": title, "body": body,
                        "owner_registration_active": True,
                        "pinned_public_ip_used": True,
                        "signed_in_site_used": False,
                        "website_changed": False,
                        "javascript_executed": False,
                        "general_private_automation": False,
                    }
                finally:
                    await context.close()
            finally:
                await browser.close()
