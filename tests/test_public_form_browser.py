"""TinyFish-free public-form browser task contract (no live accounts)."""
import json
from pathlib import Path
import unittest

from plenum_ai.public_form_browser import (
    AUTHOR, SCHEMA, TITLE, validate_request, build_public_get_target, report
)

BASE = {
    "schema": SCHEMA,
    "url": "https://arxiv.org/",
    "form_selector": "form#search-form",
    "field_selector": "input[name=query]",
    "query": "stellar spectra",
}


class PublicFormBrowserContract(unittest.TestCase):
    def test_only_exact_founder_schema_and_queryless_approved_page(self):
        body = json.dumps(BASE)
        self.assertEqual(validate_request(AUTHOR,TITLE,body)["query"],"stellar spectra")
        for author,title,payload in [
            ("other-owner",TITLE,BASE),
            (AUTHOR,"prometheus",BASE),
            (AUTHOR,TITLE,{**BASE,"query":" hello "}),
            (AUTHOR,TITLE,{**BASE,"query":"private\npassword"}),
            (AUTHOR,TITLE,{**BASE,"url":"https://arxiv.org/?token=secret"}),
            (AUTHOR,TITLE,{**BASE,"url":"https://127.0.0.1"}),
            (AUTHOR,TITLE,{**BASE,"url":"https://evil.example"}),
            (AUTHOR,TITLE,{**BASE,"extra":"unexpected"}),
            (AUTHOR,TITLE,{**BASE,"field_selector":""}),
            (AUTHOR,TITLE,{**BASE,"query":"x"*121}),
        ]:
            with self.subTest(author=author, payload=str(payload)[:45]):
                with self.assertRaises((ValueError,PermissionError)):
                    validate_request(author,title,json.dumps(payload))

    def test_explicit_public_get_parameters_are_bounded_and_safe(self):
        payload={**BASE,"parameters":{"searchtype":"all"}}
        self.assertEqual(
            validate_request(AUTHOR,TITLE,json.dumps(payload))["parameters"],
            {"searchtype":"all"},
        )
        url=build_public_get_target(
            "https://arxiv.org/search/","/search/","GET",
            "query","dark energy",{"searchtype":"all"}
        )
        self.assertEqual(url,"https://arxiv.org/search/?query=dark+energy&searchtype=all")
        for bad in [
            {"token":"abc"},
            {"session_id":"A"},
            {"auth_code":"A"},
            {"searchtype":"z"*71},
            {"a":"v","b":"v","c":"v","d":"v","e":"v"},
        ]:
            with self.assertRaises((ValueError,PermissionError)):
                validate_request(AUTHOR,TITLE,json.dumps({**BASE,"parameters":bad}))
        with self.assertRaises(PermissionError):
            build_public_get_target("https://arxiv.org/","/search","GET",
                                    "query","hi",{"query":"override"})

    def test_never_submit_post_or_leave_public_host(self):
        result=build_public_get_target(
            "https://arxiv.org/", "/search", "GET", "query", "dark energy"
        )
        self.assertEqual(result,"https://arxiv.org/search?query=dark+energy")
        for args in [
            ("https://arxiv.org/","/search","POST","query","a"),
            ("https://arxiv.org/","https://example.com/","GET","query","a"),
            ("https://arxiv.org/","javascript:alert(1)","GET","query","a"),
            ("https://arxiv.org/","https://127.0.0.1/","GET","query","a"),
            ("https://arxiv.org/","/search?secret=1","GET","query","a"),
            ("https://arxiv.org/","/search","GET","bad name","a"),
        ]:
            with self.subTest(args=args),self.assertRaises(PermissionError):
                build_public_get_target(*args)

    def test_public_result_does_not_claim_private_control(self):
        result={"schema":"test","account_login_or_cookies_used":False,"TinyFish_used":False}
        md=report(result)
        self.assertIn("Public GET search only",md)
        self.assertIn("TinyFish_used",md)
        source=(Path(__file__).resolve().parents[1]/
                "src/plenum_ai/public_form_browser.py").read_text()
        self.assertIn('request.method != "GET"',source)
        self.assertIn("page.goto(",source)
        self.assertNotIn("requestSubmit(",source)
        self.assertNotIn("BrowserProfileStore",source)
        self.assertNotIn("COMPUTER_BROWSER_TOKEN",source)


    def test_only_owner_can_inspect_public_form_metadata(self):
        from plenum_ai.public_form_browser import (
            INSPECT_TITLE, INSPECT_SCHEMA, validate_inspect_request, _public_html_attr
        )
        task={"schema":INSPECT_SCHEMA,"url":"https://arxiv.org/search/"}
        self.assertEqual(validate_inspect_request(AUTHOR,INSPECT_TITLE,json.dumps(task)),task)
        for bad in [
            (AUTHOR,INSPECT_TITLE,{"schema":INSPECT_SCHEMA,"url":"https://private.example"}),
            ("other",INSPECT_TITLE,task),
            (AUTHOR,INSPECT_TITLE,{"schema":INSPECT_SCHEMA,"url":"https://arxiv.org/?token=abc"}),
        ]:
            with self.assertRaises((ValueError,PermissionError)):
                validate_inspect_request(bad[0],bad[1],json.dumps(bad[2]))
        self.assertEqual(_public_html_attr('query" SECRET <here>'),"querySECREThere")

if __name__=="__main__":
    unittest.main()
