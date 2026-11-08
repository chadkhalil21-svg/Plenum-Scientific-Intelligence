"""Offline cryptographic and tool-boundary tests, no real OAuth or Cloud Run calls."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from services.computer_browser.oauth_resource_boundary import (
    ResourceConfig, OwnerJWTVerifier, enforce_verified_claims,
    validate_public_machine_result, read_fixed_public_fixture,
)

ISSUER="https://plenum-test.us.auth0.com/"
RESOURCE="https://browser.plenum.example/mcp"
CLIENT="https://chatgpt.com/oauth/client.json"
WORKER="https://plenum-computer-browser-machine-98614162800.us-east1.run.app"
OWNER="auth0|synthetic-owner-credential-never-real"
CFG=ResourceConfig(
    issuer=ISSUER, resource=RESOURCE,
    jwks_url="https://plenum-test.us.auth0.com/.well-known/jwks.json",
    owner_sub=OWNER, client_id=CLIENT, machine_url=WORKER,
)
FIXTURE={
    "schema":"plenum-private-browser-read-v1",
    "final_url":"https://example.com/",
    "status":200,
    "title_untrusted":"Example Domain",
    "body_excerpt_untrusted":"Example Domain. This domain is for examples.",
    "external_site_changed":False,
    "authenticated_site_used":False,
    "AGI_demonstrated":False,
}


class ConfigAndPolicyTests(unittest.TestCase):
    def test_configuration_is_explicit_and_exact(self):
        self.assertEqual(CFG.validate(),CFG)
        for field,value in (
            ("issuer","http://plenum-test.us.auth0.com/"),
            ("resource","https://127.0.0.1/mcp"),
            ("jwks_url","https://other.example/.well-known/jwks.json"),
            ("owner_sub",""),
            ("client_id",""),
            ("machine_url","https://example.com"),
            ("machine_url", RESOURCE),
            ("resource", WORKER + "/mcp"),
        ):
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                replace(CFG,**{field:value}).validate()
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):
                ResourceConfig.from_environment()

    def test_verified_claims_are_exactly_owner_client_resource_and_read_only(self):
        now=int(time.time())
        claims={"iss":ISSUER,"aud":RESOURCE,"sub":OWNER,"azp":CLIENT,
                "iat":now-5,"exp":now+200,"scope":"browser:read"}
        ok=enforce_verified_claims(claims,CFG,now=now)
        self.assertTrue(ok["subject_verified"])
        self.assertEqual(ok["scopes"],["browser:read"])
        for field,value in (
            ("iss","https://attacker.example/"),
            ("aud","https://other.example/mcp"),
            ("aud",[RESOURCE,"https://attacker.example/"]),
            ("sub","auth0|someone-else"),
            ("azp","https://other-client.example/client"),
            ("scope","browser:write"),
            ("exp",now-1),("exp",now+1200),
            ("iat",now+1200),("iat",True),
        ):
            with self.subTest(field=field), self.assertRaises(PermissionError):
                enforce_verified_claims({**claims,field:value},CFG,now=now)
        with self.assertRaises(PermissionError):
            enforce_verified_claims({k:v for k,v in claims.items() if k!="azp"},CFG,now=now)

    def test_machine_output_never_returns_unknown_secret_fields(self):
        good=validate_public_machine_result({**FIXTURE,
            "cookies":["fake"],"headers":{"Authorization":"fake"},
            "raw_html":"not-to-be-sent"})
        self.assertEqual(good["title_untrusted"],"Example Domain")
        self.assertFalse(good["private_session_access"])
        self.assertNotIn("cookies",good)
        self.assertNotIn("headers",good)
        self.assertNotIn("raw_html",good)
        for updates in (
            {"schema":"fake"},
            {"status":401},
            {"final_url":"https://private.example/"},
            {"external_site_changed":True},
            {"authenticated_site_used":True},
            {"AGI_demonstrated":True},
            {"title_untrusted":"a"*901},
            {"body_excerpt_untrusted":"a"*901},
        ):
            with self.subTest(updates=updates),self.assertRaises(PermissionError):
                validate_public_machine_result({**FIXTURE,**updates})


class SignedJWTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        cls.jwt=jwt
        cls.priv=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.pub=cls.priv.public_key()

    def make_token(self,**changes):
        now=int(time.time())
        claims={"iss":ISSUER,"aud":RESOURCE,"sub":OWNER,"azp":CLIENT,
                "iat":now-10,"exp":now+120,"scope":"browser:read"}
        claims.update(changes)
        return self.jwt.encode(claims,self.priv,algorithm="RS256",headers={"kid":"synthetic-rotation-key"})

    def test_real_rsa_signature_and_policy_verify_with_mocked_jwks_transport(self):
        class KeySource:
            def __init__(self,url,**kwargs):
                self.url=url
            def get_signing_key_from_jwt(self,token):
                from types import SimpleNamespace
                return SimpleNamespace(key=self_key)
        self_key=self.pub
        with patch.object(self.jwt,"PyJWKClient",KeySource):
            verifier=OwnerJWTVerifier(CFG)
            ok=verifier.verify(self.make_token())
            self.assertTrue(ok["subject_verified"])
            for changes in (
                {"aud":"https://attacker.example/mcp"},
                {"iss":"https://attacker.example/"},
                {"azp":"malicious-client"},
                {"sub":"another-owner"},
                {"scope":"browser:write"},
                {"exp":int(time.time())-30},
                {"exp":int(time.time())+1200},
            ):
                with self.subTest(changes=changes),self.assertRaises(PermissionError):
                    verifier.verify(self.make_token(**changes))
            bad=self.jwt.encode(
                {"iss":ISSUER,"aud":RESOURCE,"sub":OWNER,"azp":CLIENT,
                 "iat":int(time.time()),"exp":int(time.time())+100,"scope":"browser:read"},
                rsa_other_key(),algorithm="RS256",headers={"kid":"synthetic-rotation-key"})
            with self.assertRaises(PermissionError):
                verifier.verify(bad)
            with self.assertRaises(PermissionError):
                verifier.verify("not-a-JWT")
            with self.assertRaises(PermissionError):
                verifier.verify(self.jwt.encode(
                    {"iss":ISSUER,"aud":RESOURCE,"sub":OWNER,"azp":CLIENT,
                     "iat":int(time.time()),"exp":int(time.time())+100,"scope":"browser:read"},
                    "guessable-test-key",algorithm="HS256",headers={"kid":"bad"}))


def rsa_other_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    return rsa.generate_private_key(public_exponent=65537,key_size=2048)


class IAMWorkerAdapterTests(unittest.TestCase):
    def test_exact_iam_only_machine_route_no_key_file_no_session(self):
        import httpx
        from google.oauth2 import id_token
        from types import SimpleNamespace
        sent=[]
        class FakeClient:
            def __init__(self,**kwargs):
                self.options=kwargs
            async def __aenter__(self):
                return self
            async def __aexit__(self,*args):
                return False
            async def post(self,url,**kwargs):
                sent.append((url,kwargs,self.options))
                return SimpleNamespace(
                    status_code=200,content=json.dumps(FIXTURE).encode(),
                    json=lambda:FIXTURE,
                )
        with patch.object(id_token,"fetch_id_token",return_value="synthetic-google-id-token"),patch.object(
            httpx,"AsyncClient",FakeClient
        ):
            result=asyncio.run(read_fixed_public_fixture(CFG))
        self.assertEqual(len(sent),1)
        url,kwargs,options=sent[0]
        self.assertEqual(url,WORKER+"/machine/v1/public-read")
        self.assertEqual(kwargs["json"],{"url":"https://example.com/"})
        self.assertEqual(kwargs["headers"]["Authorization"],"Bearer synthetic-google-id-token")
        self.assertFalse(options["follow_redirects"])
        self.assertFalse(options["trust_env"])
        self.assertFalse(result["private_session_access"])
        self.assertNotIn("cookies",result)

    def test_wrong_worker_identity_fails_before_any_http(self):
        with self.assertRaises(ValueError):
            asyncio.run(read_fixed_public_fixture(replace(CFG,machine_url="https://attacker.example")))


class MCPFacadeTransportTests(unittest.TestCase):
    def test_sdk_publishes_resource_and_blocks_unsigned_mcp_tool_requests(self):
        from starlette.testclient import TestClient
        from services.computer_browser.mcp_resource_server import create_private_browser_mcp
        env={
            "PLENUM_MCP_OAUTH_ISSUER":ISSUER,
            "PLENUM_MCP_RESOURCE_URL":RESOURCE,
            "PLENUM_MCP_OAUTH_JWKS_URL":CFG.jwks_url,
            "PLENUM_MCP_OWNER_SUB":OWNER,
            "PLENUM_MCP_ALLOWED_CLIENT_ID":CLIENT,
            "PLENUM_MCP_MACHINE_URL":WORKER,
        }
        with patch.dict(os.environ,env,clear=True):
            server=create_private_browser_mcp()
            app=server.streamable_http_app()
            with TestClient(app) as client:
                metadata=client.get("/.well-known/oauth-protected-resource/mcp")
                self.assertEqual(metadata.status_code,200)
                self.assertEqual(metadata.json()["resource"],RESOURCE)
                self.assertIn(ISSUER.rstrip("/"),[
                    x.rstrip("/") for x in metadata.json()["authorization_servers"]
                ])
                request=client.post("/mcp",json={
                    "jsonrpc":"2.0","id":1,
                    "method":"tools/list","params":{}
                },headers={"Accept":"application/json, text/event-stream"})
                self.assertEqual(request.status_code,401)
                self.assertIn("resource_metadata=",request.headers.get("www-authenticate","").lower())
                self.assertNotIn("example.com",request.text)

    def test_sdk_does_not_construct_server_with_missing_owner_config(self):
        from services.computer_browser.mcp_resource_server import create_private_browser_mcp
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):
                create_private_browser_mcp()


class MCPFacadeSourceTests(unittest.TestCase):
    def test_no_std_io_or_unauthenticated_browser_tools(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"services/computer_browser/mcp_resource_server.py").read_text()
        self.assertIn('server.run(transport="streamable-http")',source)
        self.assertIn("validate_token_resource=True",source)
        self.assertIn("required_scopes=[READ_SCOPE]",source)
        self.assertEqual(source.count('"securitySchemes"'),2)
        self.assertIn("require_owner()",source)
        self.assertIn("bearer.subject != config.owner_sub",source)
        self.assertIn("bearer.client_id != config.client_id",source)
        self.assertNotIn('transport="stdio"',source)
        self.assertNotIn("auth_server_provider=",source)
        self.assertNotIn("client_secret",source)


if __name__=="__main__":
    unittest.main()
