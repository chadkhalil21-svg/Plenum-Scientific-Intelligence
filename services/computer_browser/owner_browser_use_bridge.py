"""Trusted local handoff from existing encrypted Plenum owner sessions to Browser Use.

No API route, ChatGPT tool, website write authorization or credential manager.
Only the private Auth0 owner backend may call this after verifying identity;
never expose the returned Browser object or state over GitHub / HTTP.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from .engine import safe_url
from .owner_live_access import owner_live_origin
from .private_profiles import BrowserProfileStore
from .session_crypto import filter_site_storage

_PROXY_PORT = re.compile(r"^http://127[.]0[.]0[.]1:([0-9]{2,5})$")


def _private_proxy(proxy: str) -> str:
    # A pinned public-IP CONNECT proxy must already be running in the SAME
    # owner server process. No Internet-facing/CDP proxy or credentials.
    if not isinstance(proxy, str):
        raise PermissionError("Original private proxy required")
    m = _PROXY_PORT.fullmatch(proxy)
    if not m or not 1 <= int(m.group(1)) <= 65535:
        raise PermissionError("Original loopback-only proxy required")
    return proxy


def _exact_origin(site: str) -> str:
    if not isinstance(site, str) or len(site) > 253:
        raise PermissionError("Exact owner site required")
    try:
        p = urlsplit(site)
        if (p.scheme != "https" or not p.hostname or p.port is not None
                or p.username is not None or p.password is not None
                or p.path or p.query or p.fragment
                or site != f"https://{p.hostname}"):
            raise PermissionError("Exact owner site required")
    except ValueError as exc:
        raise PermissionError("Exact owner site required") from None
    if not safe_url(site, origins={site}):
        raise PermissionError("Unsafe website origin")
    return site


def build_private_browser_use(
    *, verified_owner: dict, website_origin: str, owner_proxy_url: str,
    existing_chromium_executable: str, store=None, browser_factory=None,
):
    """Create Browser Use using ORIGINAL Chromium and GCS session IN MEMORY.

    Must be invoked only by an already-verified owner backend and a currently
    active original PinnedOriginProxy. Its caller must enforce the original
    owner_task_loop consent and verification callbacks BEFORE any model-driven
    action. Constructing the Browser is NOT authorization to submit a form.
    """
    if (not isinstance(verified_owner, dict)
            or not isinstance(verified_owner.get("private_owner_id"), str)
            or not verified_owner["private_owner_id"]):
        raise PermissionError("Verified owner session required")
    owner_id = verified_owner["private_owner_id"]
    origin = _exact_origin(website_origin)
    scoped_origin, dynamic = owner_live_origin(owner_id=owner_id, site=origin)
    if scoped_origin != origin or not dynamic:
        raise PermissionError("Current owner website grant required")
    proxy_url = _private_proxy(owner_proxy_url)
    if (not isinstance(existing_chromium_executable, str)
            or not existing_chromium_executable.startswith("/ms-playwright/")
            or ".." in existing_chromium_executable.split("/")):
        raise PermissionError("Only original installed Chromium permitted")
    if store is None:
        store = BrowserProfileStore.from_environment()
    try:
        saved_state, generation = store.load_for_trusted_worker(
            owner=owner_id, origin=origin)
    except Exception:
        # Do not expose GCS paths/generations/credential values in errors.
        raise PermissionError("No valid original owner session available") from None
    if type(generation) is not int or generation < 1 or not isinstance(saved_state, dict):
        raise PermissionError("Invalid saved session metadata")
    # Strip other login providers' cookies/IndexedDB even when storage was
    # imported by earlier generations of the owner's vault.
    state = filter_site_storage(saved_state, origin)
    if not state["cookies"] and not state["origins"]:
        raise PermissionError("No website session state to restore")

    if browser_factory is None:
        # Existing official pinned browser-use==0.13.14 package, not an
        # invented agent, new browser provider, or paid cloud account.
        from browser_use import Browser
        from browser_use.browser.profile import ProxySettings
        browser_factory = Browser
        proxy = ProxySettings(server=proxy_url)
    else:
        # Injected factory for no-network security/contract tests.
        proxy = {"server": proxy_url}

    return browser_factory(
        headless=True, use_cloud=False, is_local=True, keep_alive=False,
        cdp_url=None,
        executable_path=existing_chromium_executable,
        storage_state=state,
        user_data_dir=None,
        proxy=proxy,
        allowed_domains=[origin],
        block_ip_addresses=True,
        enable_default_extensions=False,
        args=["--disable-background-networking", "--disable-quic",
              "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
    )
