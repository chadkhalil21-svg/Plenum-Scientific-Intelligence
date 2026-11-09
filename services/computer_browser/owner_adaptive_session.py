"""Short-lived, owner-approved adaptive READ-ONLY saved-site navigation.

This is an adapter to the EXISTING owner Auth0, encrypted GCS, GitHub OIDC,
recipient-only sealed results, and original Chromium saved session. The public
GitHub issue carries ONLY a random cursor and link index, never a URL, cookie,
site, login, private page or action plan. One owner consent permits at most
three follow-up reads of exact same-site links returned by a previous read.

No arbitrary URL requests, submissions, account changes, scripts, uploads,
file downloads, private network access, general action-agent, or site bypass.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import time

CURSOR_BLOB = "browser-chat-read/v3/owner-adaptive-cursor.sealed"
FLAG = "PLENUM_ADAPTIVE_OWNER_READ_ENABLED"
MAX_FOLLOWS = 3
TTL = 600
_ID = re.compile(r"[0-9a-f]{32}")


def require_enabled():
    from .sealed_chat_read import require_enabled as require_sealed
    require_sealed()
    if os.environ.get(FLAG) != "true":
        raise PermissionError("Adaptive private read is disabled")


def _validate_id(value):
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise PermissionError("Invalid owner browser cursor")
    return value


def _safe_links(site, path, result):
    """Restrict original read-only link hints to non-action paths.

    A link is only a candidate for another HTTPS GET. Never execute an
    arbitrary instruction or path supplied in page text.
    """
    from .owner_saved_session import _approved_batch_paths
    from .sealed_chat_read import _validate_intent
    if not isinstance(result, dict) or result.get("site") != site:
        raise PermissionError("Saved owner page mismatch")
    if (result.get("final_url") != site + path
            or type(result.get("http_status")) is not int
            or result["http_status"] != 200):
        raise PermissionError("Saved owner page URL mismatch")
    links = result.get("links_untrusted", [])
    if not isinstance(links, list) or len(links) > 6:
        raise PermissionError("Malformed navigation links")
    candidates = []
    seen = set()
    for link in links:
        if not isinstance(link, dict) or set(link) != {"label_untrusted", "path"}:
            raise PermissionError("Malformed navigation link")
        name, relative = link["label_untrusted"], link["path"]
        if (not isinstance(name, str) or not 1 <= len(name) <= 75
                or any(ord(c) < 32 for c in name)
                or not isinstance(relative, str)):
            continue
        try:
            _approved_batch_paths(site, path, [relative])
        except PermissionError:
            continue
        if relative in seen:
            continue
        candidates.append({"label_untrusted": name, "path": relative})
        seen.add(relative)
    return candidates


def _cursor_blob():
    from .sealed_chat_read import _store
    return _store().bucket.blob(CURSOR_BLOB)


def _cipher():
    from .sealed_chat_read import _cipher as existing_cipher
    return existing_cipher()


def _check_scope(record, now):
    from .sealed_chat_read import _validate_intent
    from .owner_chat_pairing import _owner
    keys = {"schema", "session_id", "owner", "site",
            "path", "recipient_public_key", "issued",
            "expires", "remaining", "links"}
    if (not isinstance(record, dict)
            or set(record) not in (keys, keys | {"lease"})
            or ("lease" in record and _ID.fullmatch(str(record["lease"])) is None)
            or record.get("schema") != "plenum-adaptive-read-cursor-v1"
            or not _ID.fullmatch(str(record.get("session_id", "")))
            or type(record.get("issued")) is not int
            or type(record.get("expires")) is not int
            or type(record.get("remaining")) is not int
            or not 0 <= record["remaining"] <= MAX_FOLLOWS
            or not 0 < record["expires"] - record["issued"] <= TTL
            or record["issued"] > now + 10
            or record["expires"] <= now
            or not isinstance(record.get("links"), list)
            or len(record["links"]) > 6):
        raise PermissionError("Expired or malformed browser navigation approval")
    _owner(record["owner"])
    _validate_intent(site=record["site"], path=record["path"],
                     recipient_public_key=record["recipient_public_key"])
    # Revalidate every proposed link against the current approved origin.
    _safe_links(record["site"], record["path"], {
        "site": record["site"],
        "final_url": record["site"] + record["path"],
        "http_status": 200,
        "links_untrusted": record["links"],
    })
    return record


def begin_session(consent, result, *, now=None):
    """After first exact owner-approved read, create a bounded cursor.

    Replaces only the existing previous owner cursor, never a browser
    credential. Storage is private/FERNET-encrypted with GCS CAS.
    """
    require_enabled()
    t = int(time.time() if now is None else now)
    from .sealed_chat_read import _validate_intent
    if (not isinstance(consent, dict)
            or consent.get("schema") != "plenum-sealed-owner-adaptive-consent-v1"
            or type(consent.get("issued")) is not int
            or type(consent.get("expires")) is not int
            or consent["expires"] <= t
            or consent["issued"] > t + 10
            or not 0 < consent["expires"] - consent["issued"] <= TTL):
        raise PermissionError("Owner adaptive approval missing or expired")
    session_id = _validate_id(consent.get("adaptive_session_id"))
    _validate_intent(site=consent.get("site"), path=consent.get("path"),
                     recipient_public_key=consent.get("recipient_public_key"))
    links = _safe_links(consent["site"], consent["path"], result)
    record = {
        "schema": "plenum-adaptive-read-cursor-v1",
        "session_id": session_id,
        "owner": consent["owner"],
        "site": consent["site"],
        "path": consent["path"],
        "recipient_public_key": consent["recipient_public_key"],
        "issued": consent["issued"],
        "expires": consent["expires"],
        "remaining": MAX_FOLLOWS,
        "links": links,
    }
    _check_scope(record, t)
    blob = _cursor_blob()
    generation = 0
    if blob.exists():
        blob.reload()
        generation = int(blob.generation)
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(record, separators=(",", ":")).encode()),
        content_type="application/octet-stream",
        if_generation_match=generation,
    )
    return {"session_id": session_id, "remaining": MAX_FOLLOWS,
            "links_untrusted": links}


def consume_follow(session_id, link_index, *, now=None):
    """Signed OIDC workflow ONLY: one GCS CAS deletion before visiting link."""
    require_enabled()
    t = int(time.time() if now is None else now)
    _validate_id(session_id)
    if type(link_index) is not int or not 1 <= link_index <= 6:
        raise PermissionError("Invalid browser link number")
    blob = _cursor_blob()
    try:
        blob.reload()
        generation = int(blob.generation)
        sealed = blob.download_as_bytes(if_generation_match=generation)
        state = json.loads(_cipher().decrypt(sealed, ttl=TTL))
        _check_scope(state, t)
        if ("lease" in state
                or state["session_id"] != session_id
                or state["remaining"] < 1
                or link_index > len(state["links"])):
            raise PermissionError("Unapproved browser link or expired scope")
        path = state["links"][link_index - 1]["path"]
        if path == state["path"]:
            raise PermissionError("Repeated private link navigation")
        # Atomic lease prevents replay, and permits owner revocation while a
        # Chromium read is running. The worker must complete against THIS
        # generation; it cannot resurrect a revoked cursor.
        lease = secrets.token_hex(16)
        in_flight = {**state, "lease": lease}
        blob.upload_from_string(
            _cipher().encrypt(json.dumps(in_flight, separators=(",", ":")).encode()),
            content_type="application/octet-stream",
            if_generation_match=generation,
        )
        return {**state, "path": path, "remaining": state["remaining"] - 1,
                "lease": lease}
    except Exception as exc:
        raise PermissionError("Owner-approved browser link unavailable") from exc


def save_follow(cursor, result, *, now=None):
    """Update encrypted cursor after one successful exact private page."""
    require_enabled()
    t = int(time.time() if now is None else now)
    if not isinstance(cursor, dict):
        raise PermissionError("Invalid active browser cursor")
    links = _safe_links(cursor["site"], cursor["path"], result)
    if not _ID.fullmatch(str(cursor.get("lease", ""))):
        raise PermissionError("Signed navigation lease missing")
    blob = _cursor_blob()
    try:
        blob.reload()
        generation = int(blob.generation)
        leased = json.loads(_cipher().decrypt(
            blob.download_as_bytes(if_generation_match=generation), ttl=TTL
        ))
        _check_scope(leased, t)
        if (leased.get("lease") != cursor["lease"]
                or leased["session_id"] != cursor["session_id"]
                or leased["owner"] != cursor["owner"]
                or leased["site"] != cursor["site"]
                or leased["remaining"] != cursor["remaining"] + 1):
            raise PermissionError("Owner revoked or changed navigation lease")
        state = {**cursor, "links": links}
        state.pop("lease")
        _check_scope(state, t)
        if state["remaining"] == 0:
            blob.delete(if_generation_match=generation)
        else:
            blob.upload_from_string(
                _cipher().encrypt(json.dumps(state, separators=(",", ":")).encode()),
                content_type="application/octet-stream",
                if_generation_match=generation,
            )
    except Exception as exc:
        raise PermissionError("Adaptive follow-up was revoked or expired") from exc
    return {"remaining": state["remaining"], "links_untrusted": links}


def revoke_session(*, owner=None):
    """Owner-only cancellation of BOTH pending and active adaptive consent.

    This also rejects a stale in-flight worker's attempt to republish a
    deleted CAS lease. A pending fixed-batch read is deliberately unaffected.
    """
    require_enabled()
    from .sealed_chat_read import APPROVAL_BLOB, _store
    from .owner_chat_pairing import _owner
    if owner is not None:
        _owner(owner)
    revoked = False

    # The signed founder may revoke before the FIRST GitHub issue starts.
    pending = _store().bucket.blob(APPROVAL_BLOB)
    if pending.exists():
        pending.reload()
        generation = int(pending.generation)
        record = json.loads(_cipher().decrypt(
            pending.download_as_bytes(if_generation_match=generation), ttl=TTL
        ))
        if record.get("schema") == "plenum-sealed-owner-adaptive-consent-v1":
            if owner is not None and record.get("owner") != owner:
                raise PermissionError("Pending adaptive consent is not this owner")
            pending.delete(if_generation_match=generation)
            revoked = True

    # The same founder may revoke after the initial page or during a follow.
    active = _cursor_blob()
    if active.exists():
        active.reload()
        generation = int(active.generation)
        record = json.loads(_cipher().decrypt(
            active.download_as_bytes(if_generation_match=generation), ttl=TTL
        ))
        if owner is not None and record.get("owner") != owner:
            raise PermissionError("Adaptive session is not this owner")
        active.delete(if_generation_match=generation)
        revoked = True
    return revoked

async def read_hardened_saved_site(*, site, owner, path):
    """Restore original encrypted profile in Chromium with ONE pinned HTTPS egress.

    Read-only, no JavaScript, no external subresources, GET exact document only.
    This uses the existing Playwright runtime and existing public-preview
    pinned-IP CONNECT broker, never a second browser architecture.
    """
    import asyncio
    from urllib.parse import urlsplit
    from .owner_saved_session import (
        _approved_read_target, _validated_read_links, PUBLIC_DEMO_ORIGIN
    )
    from .private_profiles import BrowserProfileStore
    from .pinned_public_preview import PinnedOriginProxy
    from playwright.async_api import async_playwright
    from .engine import allowed_origins

    require_enabled()
    if site not in allowed_origins():
        raise PermissionError("Owner signed-in site has not been authorized")
    target = _approved_read_target(site, path)
    store = BrowserProfileStore.from_environment()
    state, _generation = store.load_for_trusted_worker(owner=owner, origin=site)
    async with PinnedOriginProxy(site) as broker:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-background-networking", "--disable-quic",
                      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                proxy={"server": f"http://127.0.0.1:{broker.port}"}
            )
            try:
                context = await browser.new_context(
                    storage_state=state, accept_downloads=False,
                    java_script_enabled=False, service_workers="block",
                    ignore_https_errors=False, permissions=[],
                )
                try:
                    async def restrict(route):
                        req = route.request
                        if (req.method == "GET"
                                and req.resource_type == "document"
                                and req.url == target):
                            await route.continue_()
                        else:
                            await route.abort()
                    await context.route("**/*", restrict)
                    page = await context.new_page()
                    response = await page.goto(
                        target, wait_until="domcontentloaded", timeout=22000
                    )
                    if (response is None or response.status != 200
                            or page.url != target or broker.accepted < 1):
                        raise PermissionError("Private pinned read left approved page")
                    title = " ".join((await page.title()).split())[:160]
                    body = " ".join((await page.locator("body").inner_text(
                        timeout=7000)).split())[:1200]
                    links = []
                    anchors = page.locator("a[href]")
                    for i in range(min(await anchors.count(), 18)):
                        link = anchors.nth(i)
                        try:
                            if not await link.is_visible():
                                continue
                            href = await link.get_attribute("href", timeout=500)
                            label = await link.inner_text(timeout=500)
                        except Exception:
                            continue
                        links.append((label, href))
                    return {
                        "site": site,
                        "final_url": page.url,
                        "http_status": response.status,
                        "title": title,
                        "body": body,
                        "links_untrusted": _validated_read_links(
                            site, target, links
                        ),
                        "demo_authenticated_restored": (
                            site == PUBLIC_DEMO_ORIGIN
                            and urlsplit(page.url).path == "/secure"
                            and "Logged in as" in body
                            and "Secure Area" in body
                        ),
                    }
                finally:
                    await context.close()
            finally:
                await browser.close()
