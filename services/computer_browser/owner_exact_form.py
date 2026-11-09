"""One exact owner-approved native HTML form POST using EXISTING saved Playwright.

No general unreviewed website mutation, checkout, bank transfer, access-grant,
password/MFA, API operation, arbitrary JavaScript or private content in GitHub.

The trusted Auth0 owner reviews the exact website, pre-GET path, form selector,
POST destination, complete fields, and a deliberately strong confirmation.
Only then can the original signed founder GitHub OIDC workflow consume the
10-minute encrypted GCS consent ONCE, before Chromium may send a form POST.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import secrets
import time
from urllib.parse import urljoin

from .engine import allowed_origins
from .owner_chat_pairing import _owner, _store, _cipher
from .private_profiles import BrowserProfileStore
from .sealed_chat_read import parse_recipient, _b64, require_enabled as require_sealed

FLAG = "PLENUM_EXACT_OWNER_FORM_POST_ENABLED"
APPROVAL_BLOB = "browser-chat-read/v4/exact-owner-form-post-once.sealed"
SCHEMA = "plenum-exact-owner-form-post-v1"
AAD = b"plenum-exact-owner-native-form-post-v1"
TTL = 600
MAX_OPERATIONS = 5
_PATH = re.compile(r"/[A-Za-z0-9/_.-]{0,219}")
_SELECTOR = re.compile(
    r"""(?:\#[A-Za-z][A-Za-z0-9_-]{0,80}|"""
    r"""(?:input|select|textarea|button)\[name=(?:(?:['"]?[A-Za-z][A-Za-z0-9_-]{0,79}['"]?)|[A-Za-z][A-Za-z0-9_-]{0,79})\]|"""
    r"""(?:button|input)\[type=submit\])"""
)
_FORM = re.compile(r"""form(?:\#[A-Za-z][A-Za-z0-9_-]{0,80}|\[name=['"]?[A-Za-z][A-Za-z0-9_-]{0,79}['"]?\])?""")
_BLOCKED = re.compile(
    r"(?i)(?:^|[/_.-])(?:billing|payments?|checkouts?|purchases?|pay|orders?|"
    r"banks?|banking|transfers?|withdraw(?:als?)?|payouts?|refunds?|"
    r"subscriptions?|credits?|tax(?:es)?|delete|remove|cancel|revoke|"
    r"disable|roles?|permissions?|access|admin|security|passwords?|"
    r"mfa|2fa|otp|secret|tokens?|api|webhook|authorize|auth|login|"
    r"logout|publish|invite|send|email)(?:[/_.-]|$)"
)
_SENSITIVE = re.compile(r"(?i)(?:password|passwd|mfa|2fa|otp|secret|token|"
                        r"key|card|cvv|ssn|pin|bank|payment|transfer|role|permission)")


def require_enabled():
    require_sealed()
    if os.environ.get(FLAG) != "true":
        raise PermissionError("Owner-reviewed form POST is not enabled")


def _path(site: str, path: str) -> str:
    # Keep scientific/core imports free of optional FastAPI/browser packages.
    from .owner_saved_session import _approved_read_target
    if (not isinstance(path, str) or _PATH.fullmatch(path) is None
            or "//" in path or any(piece in (".", "..") for piece in path.split("/"))
            or _BLOCKED.search(path)):
        raise PermissionError("Only safe exact same-site nonfinancial form paths")
    target = _approved_read_target(site, path)
    if target != site + path:
        raise PermissionError("Form path left the exact approved website")
    return target


def validate_plan(*, site, page_path, post_path, form_selector,
                  operations, recipient_public_key):
    """Reuse ORIGINAL vetted BrowserStep compiler; never translate writes."""
    from .approved_action_bridge import compile_exact_steps
    if not isinstance(site, str) or site not in allowed_origins():
        raise PermissionError("No original encrypted signed-in site allowlist")
    source, dest = _path(site, page_path), _path(site, post_path)
    if source == dest:
        raise PermissionError("A form POST must target an exact separate path")
    if not isinstance(form_selector, str) or _FORM.fullmatch(form_selector) is None:
        raise PermissionError("Invalid exact form selector")
    parse_recipient(recipient_public_key)
    if isinstance(operations, str):
        if len(operations) > 4000:
            raise PermissionError("Form action plan too long")
        try:
            operations = json.loads(operations)
        except (ValueError, TypeError) as exc:
            raise PermissionError("Invalid private form plan JSON") from exc
    if (not isinstance(operations, list)
            or not 2 <= len(operations) <= MAX_OPERATIONS):
        raise PermissionError("Only 1-4 form fields plus one submit allowed")
    if (not isinstance(operations[-1], dict)
            or operations[-1].get("op") != "click"):
        raise PermissionError("One exact final submit click is required")
    for idx, step in enumerate(operations):
        if not isinstance(step, dict):
            raise PermissionError("Invalid form step")
        op, selector = step.get("op"), step.get("selector")
        if (not isinstance(selector, str)
                or _SELECTOR.fullmatch(selector) is None
                or _SENSITIVE.search(selector)):
            raise PermissionError("Unsafe or non-CSS form field selector")
        if idx < len(operations) - 1:
            if selector.startswith("#"):
                raise PermissionError("Form fields must identify their input tag")
            if (op == "fill" and not selector.startswith(("input[", "textarea["))
                    or op == "select" and not selector.startswith("select[")):
                raise PermissionError("Field selector does not match operation")
            if (op not in {"fill", "select"}
                    or set(step) != {"op", "selector", "value"}
                    or not isinstance(step["value"], str)
                    or len(step["value"]) > 500):
                raise PermissionError("Only exact non-sensitive text/select fields")
        elif set(step) != {"op", "selector"}:
            raise PermissionError("Unexpected submit action fields")
    compiled = compile_exact_steps(
        {"origin": site, "operations": operations},
        allowed_origins={site},
    )
    return compiled


def approve_form(owner_id, *, site, page_path, post_path, form_selector,
                 operations, recipient_public_key, now=None):
    """Only after verified Auth0 owner CSRF + 'APPROVE FORM POST' confirmation."""
    require_enabled()
    owner = _owner(owner_id)
    compiled = validate_plan(
        site=site, page_path=page_path, post_path=post_path,
        form_selector=form_selector, operations=operations,
        recipient_public_key=recipient_public_key
    )
    if isinstance(operations, str):
        operations = json.loads(operations)
    store = BrowserProfileStore.from_environment()
    if store.status(owner=owner, origin=site).get("profile_exists") is not True:
        raise PermissionError("No encrypted approved owner website session")
    t = int(time.time() if now is None else now)
    record = {
        "schema": SCHEMA, "owner": owner, "site": site,
        "page_path": page_path, "post_path": post_path,
        "form_selector": form_selector, "operations": operations,
        "recipient_public_key": recipient_public_key,
        "issued": t, "expires": t + TTL, "nonce": secrets.token_hex(16),
    }
    blob = _store().bucket.blob(APPROVAL_BLOB)
    generation = 0
    if blob.exists():
        blob.reload()
        generation = int(blob.generation)
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(record, separators=(",", ":")).encode()),
        content_type="application/octet-stream", if_generation_match=generation
    )
    return {"approved_once": True, "expires_in_seconds": TTL,
            "fields_count": len(compiled.steps)-1}


def consume_form(*, now=None):
    """After exact signed GitHub OIDC verification, one-time CAS consume."""
    require_enabled()
    t = int(time.time() if now is None else now)
    blob = _store().bucket.blob(APPROVAL_BLOB)
    try:
        blob.reload()
        gen = int(blob.generation)
        record = json.loads(_cipher().decrypt(
            blob.download_as_bytes(if_generation_match=gen), ttl=TTL
        ))
        expected = {"schema", "owner", "site", "page_path", "post_path",
                    "form_selector", "operations", "recipient_public_key",
                    "issued", "expires", "nonce"}
        if (not isinstance(record, dict) or set(record) != expected
                or record["schema"] != SCHEMA
                or type(record["issued"]) is not int
                or type(record["expires"]) is not int
                or not 0 < record["expires"] - record["issued"] <= TTL
                or record["issued"] > t + 10 or record["expires"] <= t
                or not isinstance(record["nonce"], str)
                or re.fullmatch(r"[0-9a-f]{32}", record["nonce"]) is None):
            raise PermissionError("Malformed one-time form approval")
        _owner(record["owner"])
        validate_plan(
            site=record["site"], page_path=record["page_path"],
            post_path=record["post_path"], form_selector=record["form_selector"],
            operations=record["operations"],
            recipient_public_key=record["recipient_public_key"],
        )
        # One-time consume occurs BEFORE any trusted saved website profile loads.
        blob.delete(if_generation_match=gen)
        return record
    except Exception as exc:
        raise PermissionError("No unconsumed owner-approved form POST") from exc


def revoke_form():
    """Authenticated owner CSRF route only. Does not modify unrelated grants."""
    require_enabled()
    blob = _store().bucket.blob(APPROVAL_BLOB)
    if not blob.exists():
        return False
    blob.reload()
    blob.delete(if_generation_match=int(blob.generation))
    return True


async def submit_native_post(*, record):
    """Native POST from EXISTING Chromium with pinned exact-site HTTPS egress.

    JavaScript and subresource traffic are off. Only the initial exact GET
    document and a single approved same-site POST document may reach network.
    An ambiguous result is never automatically retried: consent was consumed.
    """
    from .pinned_public_preview import PinnedOriginProxy
    from .browser_actions import execute_steps_on_page
    from playwright.async_api import async_playwright

    compiled = validate_plan(
        site=record["site"], page_path=record["page_path"],
        post_path=record["post_path"], form_selector=record["form_selector"],
        operations=record["operations"],
        recipient_public_key=record["recipient_public_key"]
    )
    site = record["site"]
    page_url = _path(site, record["page_path"])
    post_url = _path(site, record["post_path"])
    state, _ = BrowserProfileStore.from_environment().load_for_trusted_worker(
        owner=record["owner"], origin=site
    )
    async with PinnedOriginProxy(site) as pinned:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-background-networking", "--disable-quic",
                      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                proxy={"server": f"http://127.0.0.1:{pinned.port}"}
            )
            try:
                context = await browser.new_context(
                    storage_state=state, java_script_enabled=False,
                    accept_downloads=False, service_workers="block",
                    ignore_https_errors=False, permissions=[],
                )
                try:
                    posted = False
                    armed = False
                    async def restrict(route):
                        nonlocal posted
                        request = route.request
                        if (request.url == page_url and request.method == "GET"
                                and request.resource_type == "document"
                                and not armed):
                            await route.continue_()
                        elif (request.url == post_url and request.method == "POST"
                              and request.resource_type == "document"
                              and armed and not posted):
                            posted = True
                            await route.continue_()
                        else:
                            await route.abort()
                    await context.route("**/*", restrict)
                    page = await context.new_page()
                    first = await page.goto(
                        page_url, wait_until="domcontentloaded", timeout=22000
                    )
                    if (not first or first.status != 200 or page.url != page_url
                            or pinned.accepted < 1):
                        raise PermissionError("Original saved page was not verified")
                    form = page.locator(record["form_selector"])
                    if await form.count() != 1:
                        raise PermissionError("Approved form does not uniquely exist")
                    if (await form.get_attribute("method") or "get").lower() != "post":
                        raise PermissionError("Form is not a native POST form")
                    form_action = await form.get_attribute("action") or page_url
                    if urljoin(page_url, form_action) != post_url:
                        raise PermissionError("Form POST target is not owner-approved")
                    if (await form.get_attribute("target")) not in (None, "", "_self"):
                        raise PermissionError("Form opens an unauthorized target")
                    encoding = (await form.get_attribute("enctype") or
                                "application/x-www-form-urlencoded").lower()
                    if encoding != "application/x-www-form-urlencoded":
                        raise PermissionError("Only ordinary URL-encoded forms")
                    # Reject password/hidden/file/action controls even if
                    # they appear under a harmless CSS name.
                    for step in compiled.steps[:-1]:
                        field = form.locator(step.selector)
                        if await field.count() != 1 or not await field.is_visible():
                            raise PermissionError("Private form field is not unique and visible")
                        if step.selector.startswith("input["):
                            field_type = (await field.get_attribute("type") or "text").lower()
                            if field_type not in {"text", "search", "email",
                                                  "tel", "url", "number"}:
                                raise PermissionError("Protected or non-text field")
                    # Original step executor: a scoped form locator prevents
                    # escaping to account-level controls outside this form.
                    await execute_steps_on_page(
                        page, compiled.steps[:-1],
                        authorized_origins={site}, locator_scope=form,
                    )
                    final = compiled.steps[-1]
                    submit = form.locator(final.selector)
                    if await submit.count() != 1:
                        raise PermissionError("Approved submit control not unique")
                    if (await submit.get_attribute("type") or
                            "submit").lower() != "submit":
                        raise PermissionError("Final click is not a submit control")
                    if (await submit.get_attribute("formaction")) not in (None, "", record["post_path"], post_url):
                        raise PermissionError("Submit button overrides approved action")
                    if (await submit.get_attribute("formmethod")) not in (None, "", "post", "POST"):
                        raise PermissionError("Submit button overrides approved method")
                    if (await submit.get_attribute("formtarget")) not in (None, "", "_self"):
                        raise PermissionError("Submit redirects to other window")
                    armed = True
                    async with page.expect_response(
                        lambda response: response.url == post_url
                        and response.request.method == "POST",
                        timeout=18000,
                    ) as response_waiter:
                        await submit.click(timeout=12000, no_wait_after=True)
                    response = await response_waiter.value
                    if not posted:
                        raise PermissionError("No exact approved POST observed")
                    return {
                        "site": site, "page_path": record["page_path"],
                        "post_path": record["post_path"], "submitted_once": True,
                        "http_status": int(response.status),
                        "verified_response": 200 <= response.status < 300,
                        "manual_confirmation_recommended": True,
                    }
                finally:
                    await context.close()
            finally:
                await browser.close()


def seal_form_receipt(record, result):
    """Same original X25519/AES-256-GCM recipient-only envelope, separate AAD."""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    if (not isinstance(result, dict)
            or result.get("site") != record.get("site")
            or result.get("page_path") != record.get("page_path")
            or result.get("post_path") != record.get("post_path")
            or result.get("submitted_once") is not True
            or type(result.get("http_status")) is not int
            or not 100 <= result["http_status"] <= 599):
        raise PermissionError("Unverified exact owner form post result")
    document = {
        "schema": "plenum-owner-exact-form-post-receipt-v1",
        "site": record["site"], "page_path": record["page_path"],
        "post_path": record["post_path"],
        "http_status": result["http_status"],
        "post_request_sent_once": True,
        "verified_response": result.get("verified_response") is True,
        "manual_confirmation_recommended": True,
        "model_sent_no_credentials_to_github": True,
    }
    payload = json.dumps(document, separators=(",", ":")).encode()
    if len(payload) > 1300:
        raise PermissionError("Owner action receipt exceeds private limit")
    ephemeral = X25519PrivateKey.generate()
    shared = ephemeral.exchange(parse_recipient(record["recipient_public_key"]))
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    key = HKDF(algorithm=hashes.SHA256(), length=32,
               salt=salt, info=b"plenum-x25519-aes256-gcm-owner-page-v1").derive(shared)
    encrypted = AESGCM(key).encrypt(nonce, payload, AAD)
    pk = ephemeral.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return {
        "schema": "plenum-sealed-browser-result-v1",
        "encoding": "x25519-hkdf-sha256-aes256gcm",
        "ephemeral_public_key": _b64(pk),
        "salt": _b64(salt), "nonce": _b64(nonce),
        "ciphertext": _b64(encrypted),
        "plaintext_in_github": False,
    }
