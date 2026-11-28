"""Frozen independent read-only provider boundary acceptance."""
import io
import unittest
from unittest.mock import patch
from plenum_ai import world_horizon as h
from plenum_ai.chief_of_staff_pilot import NoRedirects

RSS=b'<rss><channel><item><title>Valid research report</title><link>https://example.org/article</link></item></channel></rss>'

class Response(io.BytesIO):
    def __init__(self,url,status=200):
        super().__init__(RSS)
        self.url=url
        self.status=status
        self.read_count=0
    def geturl(self): return self.url
    def read(self,*a):
        self.read_count+=1
        return super().read(*a)

class HorizonBoundary(unittest.TestCase):
    def test_default_feed_uses_redirect_refusal_before_request(self):
        url=h.request_url("mit_labs","public research")
        response=Response(url)
        with patch.object(h,"build_opener") as build:
            build.return_value.open.return_value=response
            # If the original implementation calls the old captured default
            # instead, avoid a real request by replacing that function's default.
            default=h.fetch_public.__defaults__
            def forbidden(*a,**kw): raise AssertionError("unrestricted default request")
            with patch.object(h,"urlopen",forbidden):
                h.fetch_public.__defaults__=(forbidden,)
                try:
                    rows=h.fetch_public("mit_labs","public research")
                finally:
                    h.fetch_public.__defaults__=default
            self.assertEqual(len(rows),1)
            self.assertTrue(any(arg is NoRedirects or isinstance(arg,NoRedirects) for arg in build.call_args.args))

    def test_injected_response_boundary_and_status(self):
        for key in ("mit_labs","gdelt_headlines","usgs_earthquakes","github_public_code","crossref_journals"):
            url=h.request_url(key,"public research")
            for returned,status in ((url,302),("https://unapproved.example/other",200)):
                with self.subTest(key=key,returned=returned,status=status):
                    r=Response(returned,status)
                    with self.assertRaises(ValueError):
                        h.fetch_public(key,"public research",opener=lambda *a,**kw:r)
                    self.assertEqual(r.read_count,0)

    def test_injected_normal_response_and_legacy_mock(self):
        url=h.request_url("mit_labs","public research")
        for r in (Response(url),io.BytesIO(RSS)):
            rows=h.fetch_public("mit_labs","public research",opener=lambda *a,**kw:r)
            self.assertEqual(len(rows),1)
            self.assertFalse(rows[0]["primary_source_verified"])
