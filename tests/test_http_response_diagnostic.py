"""Unit tests for read-only, redacted IAP HTTP 404 differential diagnosis."""
import unittest
from pathlib import Path
from services.computer_browser.http_response_diagnostic import classify, describe

ROOT = Path(__file__).resolve().parents[1]
class HttpDifferentialTests(unittest.TestCase):
    def test_fastapi_vs_google_edge_without_raw_data(self):
        signed = b'{"detail":"Not Found"}'
        unsigned = b'<html>404. That is an error. Google</html>'
        result = describe(404, signed, 404, unsigned,
                          b'HTTP/2 404\r\nContent-Type: application/json\r\nX-Secret: bearer-value\r\n')
        self.assertEqual(result["signed_body_class"], "fastapi_route_not_found")
        self.assertEqual(result["unsigned_body_class"], "google_frontend_not_found")
        self.assertEqual(result["signed_content_type_class"], "json")
        self.assertFalse(result["bodies_identical"])
        self.assertNotIn("bearer-value", str(result))
        self.assertEqual(result["root_cause"], "not_established_from_response_comparison")

    def test_identical_404_does_not_pretend_to_prove_origin(self):
        page = b"<html>IAP error: access is denied</html>"
        r = describe(404, page, 404, page, b'Content-Type: text/html\r\n')
        self.assertTrue(r["bodies_identical"])
        self.assertEqual(r["signed_body_class"], "iap_error_page")
        self.assertEqual(r["root_cause"], "not_established_from_response_comparison")
        self.assertFalse(r["raw_body_or_credentials_logged"])

    def test_classes_are_fixed_and_status_bounds(self):
        self.assertEqual(classify(b'Internal details token-secret=ABC'), "unclassified")
        for n in (-1, 600, 999):
            with self.assertRaises(ValueError):
                describe(n,b"",404,b"",b"")
        with self.assertRaises(ValueError):
            describe(404,b"",None,b"",b"")

    def test_workflow_only_safe_read_only_request_and_cleanup(self):
        w=(ROOT/".github/workflows/computer-browser-iap-health-probe.yml").read_text()
        self.assertIn("services.computer_browser.http_response_diagnostic",w)
        self.assertIn('UNAUTH_STATUS="$(curl --silent',w)
        self.assertIn('rm -f "$UNAUTH_BODY" "$RESPONSE" "$SIGNED_HEADERS"',w)
        for disallowed in ("curl --location","gcloud run deploy","gcloud run services update",
                           "gcloud iap web add-iam-policy-binding","--allow-unauthenticated","set -x"):
            self.assertNotIn(disallowed,w)

if __name__=="__main__":
    unittest.main()
