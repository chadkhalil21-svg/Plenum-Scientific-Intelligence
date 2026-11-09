"""Focused new capability: owner-reviewed ONE native POST, never live accounts."""
import asyncio
import base64
import importlib.util
import json
import os
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.computer_browser import owner_exact_form as forms

CRYPTO = importlib.util.find_spec("cryptography") is not None
FASTAPI = importlib.util.find_spec("fastapi") is not None
PLAYWRIGHT = importlib.util.find_spec("playwright") is not None

OWNER = "b" * 64
SITE = "https://the-internet.herokuapp.com"
OPS = [
    {"op":"fill","selector":"input[name=note]","value":"Synthetic reviewed note"},
    {"op":"click","selector":"button[type=submit]"},
]
ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_CHAT_RELAY_ENABLED": "true",
    "PLENUM_SEALED_CHAT_READ_ENABLED": "true",
    forms.FLAG: "true",
    "AUTH0_OWNER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_ALLOWED_ORIGINS": SITE + ",https://example.com",
    "BROWSER_PROFILE_BUCKET": "synthetic-browser-private-vault",
    "COMPUTER_BROWSER_TOKEN": "synthetic-private-approval-token-" * 2,
    "PLENUM_CHAT_RELAY_REPO_ID":"1447724141",
    "PLENUM_CHAT_RELAY_ACTOR_ID":"251133044",
}
if CRYPTO:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    ENV["BROWSER_SESSION_KEY"] = Fernet.generate_key().decode()


def keys():
    private = X25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private, forms._b64(public)


class AtomicBlob:
    def __init__(self):
        self.data = None
        self.generation = None
        self.version = 0

    def exists(self):
        return self.data is not None

    def reload(self):
        if self.data is None:
            raise RuntimeError("No approved owner form")

    def upload_from_string(self, data, *, content_type, if_generation_match):
        if (self.data is None and if_generation_match != 0
            or self.data is not None and self.generation != if_generation_match):
            raise RuntimeError("GCS CAS blocked stale grant")
        self.version += 1
        self.generation = self.version
        self.data = data

    def download_as_bytes(self, *, if_generation_match):
        if self.data is None or self.generation != if_generation_match:
            raise RuntimeError("Grant absent or stale")
        return self.data

    def delete(self, *, if_generation_match):
        if self.data is None or self.generation != if_generation_match:
            raise RuntimeError("Grant already consumed")
        self.data = None
        self.generation = None


class Store:
    def __init__(self):
        self.bucket = self
        self.obj = AtomicBlob()
    def blob(self, path):
        if path != forms.APPROVAL_BLOB:
            raise RuntimeError("Wrong private vault object")
        return self.obj


@unittest.skipUnless(CRYPTO and FASTAPI, "Existing owner portal and recipient crypto required")
class ExactFormApprovalTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.store = Store()
        self.store_patch = patch.object(forms, "_store", return_value=self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        profile = MagicMock()
        profile.status.return_value = {"profile_exists":True}
        self.profile_patch = patch.object(forms.BrowserProfileStore,
                                         "from_environment",return_value=profile)
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)

    def plan(self, **changes):
        _, public = keys()
        return {"site":SITE,"page_path":"/profile/edit",
                "post_path":"/profile/save","form_selector":"form",
                "operations":OPS,"recipient_public_key":public,**changes}

    def test_validate_strict_safe_exact_owner_form_and_reject_unreviewed_actions(self):
        accepted = forms.validate_plan(**self.plan())
        self.assertEqual([x.operation for x in accepted.steps],
                         ["fill","click"])
        bad_cases = [
            {"site":"https://evil.example.com"},
            {"page_path":"//internal.example.org"},
            {"page_path":"/profile/../admin"},
            {"page_path":"/payments/edit"},
            {"post_path":"/checkout/pay"},
            {"post_path":"/profile/edit"},
            {"post_path":"/profile/save?unsafe=1"},
            {"form_selector":"body"},
            {"operations":[{"op":"click","selector":"button[type=submit]"}]},
            {"operations":[*OPS,{"op":"click","selector":"button[type=submit]"}]},
            {"operations":[{"op":"fill","selector":"xpath=../button","value":"X"},OPS[-1]]},
            {"operations":[{"op":"fill","selector":"input[name=password]","value":"X"},OPS[-1]]},
            {"operations":[{"op":"upload","selector":"input[name=attachment]","file_id":"X"},OPS[-1]]},
            {"operations":[{"op":"fill","selector":"input[name=note]","value":"X"*501},OPS[-1]]},
        ]
        for change in bad_cases:
            with self.subTest(change=str(change)[:90]),self.assertRaises(
                (PermissionError, ValueError)):
                forms.validate_plan(**self.plan(**change))
        with patch.dict(os.environ,{forms.FLAG:"false"}), self.assertRaises(PermissionError):
            forms.require_enabled()


    def test_broader_checkbox_and_multi_control_plan_has_strict_refusals(self):
        steps = [
            {"op":"fill","selector":"textarea[name=message]","value":"Reviewed text"},
            {"op":"select","selector":"select[name=category]","value":"general"},
            {"op":"check","selector":"input[name=contact_ok]"},
            {"op":"uncheck","selector":"input[name=notify]"},
            OPS[-1],
        ]
        accepted = forms.validate_plan(**self.plan(operations=steps))
        self.assertEqual([x.operation for x in accepted.steps],
                         ["fill", "select", "check", "uncheck", "click"])
        invalid = [
            [{"op":"check","selector":"input[name=password]"}, OPS[-1]],
            [{"op":"check","selector":"button[type=submit]"}, OPS[-1]],
            [{"op":"check","selector":"input[name=contact_ok]","value":"yes"}, OPS[-1]],
            [{"op":"uncheck","selector":"select[name=category]"}, OPS[-1]],
            [{"op":"press","selector":"input[name=note]","value":"Enter"}, OPS[-1]],
            [steps[0],steps[0],OPS[-1]],
            [*steps[:4],*steps[:4],*steps[:4],OPS[-1]],
        ]
        for case in invalid:
            with self.subTest(case=str(case)[:90]), self.assertRaises(
                (PermissionError,ValueError)
            ):
                forms.validate_plan(**self.plan(operations=case))

    def test_owner_form_grant_is_encrypted_one_time_and_can_be_revoked(self):
        _, pub = keys()
        args=self.plan(recipient_public_key=pub)
        issued=forms.approve_form(OWNER, **args)
        self.assertTrue(issued["approved_once"])
        self.assertEqual(issued["fields_count"],1)
        raw=self.store.obj.data
        self.assertNotIn(b"note",raw)
        self.assertNotIn(b"Synthetic reviewed note",raw)
        self.assertNotIn(SITE.encode(),raw)
        saved=forms.consume_form()
        self.assertEqual(saved["post_path"],"/profile/save")
        with self.assertRaises(PermissionError):
            forms.consume_form()
        forms.approve_form(OWNER,**args)
        self.assertTrue(forms.revoke_form())
        with self.assertRaises(PermissionError):
            forms.consume_form()
        self.assertFalse(forms.revoke_form())

    def test_owner_post_receipt_ciphertext_only_and_wrong_key_denied(self):
        private,public=keys()
        record = {**self.plan(recipient_public_key=public),
                  "owner":OWNER}
        result = {"site":SITE,"page_path":"/profile/edit",
                  "post_path":"/profile/save","submitted_once":True,
                  "http_status":200,"verified_response":True}
        envelope = forms.seal_form_receipt(record,result)
        encoded=json.dumps(envelope)
        self.assertNotIn(SITE,encoded)
        self.assertNotIn("/profile/save",encoded)
        self.assertNotIn("Synthetic reviewed note",encoded)
        self.assertFalse(envelope["plaintext_in_github"])
        decode=lambda v:base64.urlsafe_b64decode(v+"="*(-len(v)%4))
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
        peer=X25519PublicKey.from_public_bytes(decode(envelope["ephemeral_public_key"]))
        key=HKDF(algorithm=hashes.SHA256(),length=32,
                 salt=decode(envelope["salt"]),
                 info=b"plenum-x25519-aes256-gcm-owner-page-v1").derive(private.exchange(peer))
        data=json.loads(AESGCM(key).decrypt(
            decode(envelope["nonce"]),decode(envelope["ciphertext"]),forms.AAD))
        self.assertTrue(data["post_request_sent_once"])
        self.assertEqual(data["http_status"],200)
        other,_=keys()
        wrong=HKDF(algorithm=hashes.SHA256(),length=32,
                   salt=decode(envelope["salt"]),
                   info=b"plenum-x25519-aes256-gcm-owner-page-v1").derive(other.exchange(peer))
        with self.assertRaises(Exception):
            AESGCM(wrong).decrypt(
                decode(envelope["nonce"]),decode(envelope["ciphertext"]),forms.AAD)
        for bad in [{**result,"submitted_once":False},
                    {**result,"post_path":"/evil"},
                    {**result,"http_status":None}]:
            with self.assertRaises(PermissionError):
                forms.seal_form_receipt(record,bad)


@unittest.skipUnless(CRYPTO and FASTAPI, "Existing Auth0/FastAPI dependencies required")
class ExactFormHttpTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from services.computer_browser.owner_sealed_relay import mount_owner_sealed_relay
        from services.computer_browser.owner_console import require_verified_owner
        from services.computer_browser import owner_sealed_relay as relay
        self.env=patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        app=FastAPI()
        mount_owner_sealed_relay(app)
        app.dependency_overrides[require_verified_owner]=lambda:{"private_owner_id":OWNER}
        self.client=TestClient(app)
        self.relay=relay

    def test_owner_review_requires_authenticated_identity_csrf_and_exact_phrase(self):
        from services.computer_browser.owner_saved_session import _owner_form_token
        profile=MagicMock()
        profile.status.return_value={"profile_exists":True}
        with patch.object(self.relay.BrowserProfileStore,"from_environment",
                          return_value=profile):
            page=self.client.get("/owner/chat-exact-form")
        self.assertEqual(page.status_code,200)
        self.assertIn("APPROVE FORM POST",page.text)
        self.assertIn("Revoke pending",page.text)
        _,public=keys()
        payload={"site":SITE,"page_path":"/profile/edit",
                 "post_path":"/profile/save","form_selector":"form",
                 "operations":json.dumps(OPS),
                 "recipient_public_key":public,
                 "csrf_token":_owner_form_token(OWNER,SITE,"exact_form_post"),
                 "confirmation":"APPROVE FORM POST"}
        with patch.object(self.relay,"approve_form",
                          return_value={"approved_once":True}) as issued:
            denied=self.client.post("/owner/chat-exact-form",data=payload,
                headers={"origin":"https://evil.example.org"})
            self.assertEqual(denied.status_code,403)
            self.assertFalse(issued.called)
            wrong=self.client.post("/owner/chat-exact-form",
                                   data={**payload,"confirmation":"YES"})
            self.assertEqual(wrong.status_code,403)
            valid=self.client.post("/owner/chat-exact-form",data=payload)
        self.assertEqual(valid.status_code,200)
        issued.assert_called_once()
        revoke_payload={
            "csrf_token":_owner_form_token(
                OWNER,"https://example.com","exact_form_revoke"),
            "confirmation":"REVOKE FORM"}
        with patch.object(self.relay,"revoke_form",return_value=True) as revoked:
            status=self.client.post(
                "/owner/chat-exact-form-revoke",data=revoke_payload)
        self.assertEqual(status.status_code,200)
        revoked.assert_called_once()

    def test_only_signed_founder_oidc_with_reviewed_exact_post_can_execute(self):
        from services.computer_browser.github_oidc_read_policy import GitHubOIDCTokenVerifier
        _,public=keys()
        record={"schema":forms.SCHEMA,"site":SITE,"owner":OWNER,
                "page_path":"/profile/edit","post_path":"/profile/save",
                "form_selector":"form","operations":OPS,
                "recipient_public_key":public}
        outcome={"site":SITE,"page_path":"/profile/edit",
                 "post_path":"/profile/save","submitted_once":True,
                 "http_status":200,"verified_response":True}
        with patch.object(GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}),\
             patch.object(self.relay,"consume_form",return_value=record) as consume,\
             patch.object(self.relay,"submit_native_post",
                          new_callable=AsyncMock,return_value=outcome) as run:
            anonymous=self.client.post("/internal/chat-sealed-read",
                headers={"x-plenum-action":"exact-form-post-v1"})
            self.assertEqual(anonymous.status_code,401)
            consume.assert_not_called()
            invalid=self.client.post("/internal/chat-sealed-read",
                headers={"authorization":"Bearer synthetic.signed.oidc",
                         "x-plenum-action":"arbitrary-website-write"})
            self.assertEqual(invalid.status_code,403)
            consume.assert_not_called()
            valid=self.client.post("/internal/chat-sealed-read",
                headers={"authorization":"Bearer synthetic.signed.oidc",
                         "x-plenum-action":"exact-form-post-v1"})
        self.assertEqual(valid.status_code,200)
        self.assertFalse(valid.json()["plaintext_in_github"])
        self.assertNotIn(SITE,valid.text)
        consume.assert_called_once()
        run.assert_awaited_once_with(record=record)


@unittest.skipUnless(PLAYWRIGHT and CRYPTO, "Official Playwright Chromium required")
class OfflineFormExecutorTest(unittest.TestCase):
    def test_original_browser_executor_scoped_form_without_network(self):
        from playwright.async_api import async_playwright
        from services.computer_browser.browser_actions import execute_steps_on_page

        async def run():
            site="https://example.com"
            _, pub=keys()
            ops=[{"op":"fill","selector":"input[name=note]","value":"reviewed offline"},
                 {"op":"click","selector":"button[type=submit]"}]
            with patch.dict(os.environ, {"BROWSER_ALLOWED_ORIGINS":site}):
                compiled=forms.validate_plan(
                    site=site,page_path="/profile/edit",
                    post_path="/profile/save",form_selector="form",
                    operations=ops,recipient_public_key=pub)
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(headless=True)
                try:
                    context=await browser.new_context(java_script_enabled=False)
                    async def intercept(route):
                        req=route.request
                        if req.url==site+"/profile/edit":
                            await route.fulfill(status=200,content_type="text/html",
                                body="<form method='post' action='/profile/save'>"
                                     "<input name='note'><button type='submit'>Save</button></form>")
                        elif req.url==site+"/profile/save" and req.method=="POST":
                            self.assertIn("note=reviewed",req.post_data)
                            await route.fulfill(status=200,content_type="text/html",
                                               body="<h1>Saved synthetic data</h1>")
                        else:
                            await route.abort()
                    await context.route("**/*",intercept)
                    page=await context.new_page()
                    await page.goto(site+"/profile/edit")
                    form=page.locator("form")
                    self.assertEqual(await form.count(),1)
                    await execute_steps_on_page(
                        page,compiled.steps[:-1],
                        locator_scope=form,authorized_origins={site})
                    self.assertEqual(
                        await form.locator("input[name=note]").input_value(),
                        "reviewed offline")
                    async with page.expect_response(
                        lambda rsp:rsp.url==site+"/profile/save" and
                        rsp.request.method=="POST") as pending:
                        await form.locator(compiled.steps[-1].selector).click()
                    response=await pending.value
                    self.assertEqual(response.status,200)
                    await context.close()
                finally:
                    await browser.close()
        asyncio.run(run())


if __name__=="__main__":
    unittest.main()
