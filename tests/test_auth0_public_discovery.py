"""Test public Auth0 discovery validator without network or personal data."""
import unittest
from scripts.verify_auth0_public_discovery import (
    DOMAIN,ISSUER,JWKS_URL,same_origin_url,validate_oidc,validate_jwks
)

def metadata():
    return {
        "issuer":ISSUER,
        "authorization_endpoint":ISSUER+"authorize",
        "token_endpoint":ISSUER+"oauth/token",
        "jwks_uri":JWKS_URL,
        "response_types_supported":["code","token"],
        "code_challenge_methods_supported":["S256"],
        "client_id_metadata_document_supported":False,
        "token_endpoint_auth_methods_supported":["none"],
    }

class Auth0DiscoveryTests(unittest.TestCase):
    def test_trusts_only_owner_tenant_https_urls(self):
        self.assertTrue(same_origin_url(JWKS_URL))
        for url in (None,"http://"+DOMAIN,"https://evil.example/",
                    "https://"+DOMAIN+"@evil.example/","https://"+DOMAIN+".evil.example/",
                    "https://127.0.0.1/","https://"+DOMAIN+":444/",
                    "https://"+DOMAIN+"/jwks?secret=x"):
            with self.subTest(url=url):
                self.assertFalse(same_origin_url(url))
    def test_auth_code_pkce_and_issuer_exact_required(self):
        self.assertTrue(validate_oidc(metadata())["pkce_s256_supported"])
        for key,val in (("issuer",ISSUER.rstrip("/")),
                        ("issuer","https://other.us.auth0.com/"),
                        ("code_challenge_methods_supported",["plain"]),
                        ("response_types_supported",["token"]),
                        ("jwks_uri","https://evil.example/key"),
                        ("authorization_endpoint","http://"+DOMAIN+"/authorize")):
            sample={**metadata(),key:val}
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_oidc(sample)
    def test_signing_key_required(self):
        self.assertTrue(validate_jwks({"keys":[{"kty":"RSA","kid":"kid","n":"abc","e":"AQAB"}]}))
        for bad in ({"keys":[]},{"keys":[{"kty":"oct","kid":"kid"}]},{}):
            with self.assertRaises(ValueError):
                validate_jwks(bad)
if __name__=="__main__":
    unittest.main()
