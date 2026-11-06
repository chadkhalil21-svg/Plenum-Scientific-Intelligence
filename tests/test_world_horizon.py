"""Offline public horizon contract tests: every category and failure boundary."""
import io
import json
import unittest
from urllib.parse import urlsplit
from plenum_ai.world_horizon import (
    SOURCES, CATEGORIES, REVIEW_GATED, parse_public, request_url,
    source_catalog, scan_horizon, fetch_public,
)

RSS=b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Research</title>
<item><title>Public laboratory announcement</title><link>https://news.mit.edu/example</link>
<pubDate>Fri, 06 Nov 2026 08:00:00 GMT</pubDate></item></channel></rss>'''
RDF_RSS=b'''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns="http://purl.org/rss/1.0/"
 xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>Nature journal feed</title></channel>
<item rdf:about="https://www.nature.com/articles/abc123">
<title>Measured advances in scientific discovery</title>
<link>https://www.nature.com/articles/abc123</link>
<dc:date>2026-11-06</dc:date></item>
</rdf:RDF>'''
ATOM=b'''<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>University laboratory report</title>
<link rel="alternate" href="https://news.harvard.edu/gazette/story/one"/>
<updated>2026-11-06T12:00:00Z</updated></entry></feed>'''
FIXTURES={
    "crossref":json.dumps({"message":{"items":[{"title":["Photonic research"],
        "DOI":"10.1000/photon","container-title":["Science"],
        "published":{"date-parts":[[2026,11,4]]}}]}}).encode(),
    "gdelt":json.dumps({"articles":[{"title":"Global public science policy",
        "url":"https://example.org/article","seendate":"20261106T120000Z"}]}).encode(),
    "world_bank":json.dumps([{"page":1},[{"indicator":{"value":"GDP (current US$)"},
        "value":105000,"date":"2025"}]]).encode(),
    "usgs":json.dumps({"features":[{"properties":{"title":"M 4.3 - California",
        "url":"https://earthquake.usgs.gov/earthquakes/eventpage/abc","time":12345}}]}).encode(),
    "eonet":json.dumps({"events":[{"id":"EONET_123","title":"Wildfire in region",
        "link":"https://eonet.gsfc.nasa.gov/api/v3/events/EONET_123"}]}).encode(),
    "github":json.dumps({"items":[{"full_name":"org/research-tool",
        "html_url":"https://github.com/org/research-tool","updated_at":"2026-11-06"}]}).encode(),
}

class Stream(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class WorldHorizonTests(unittest.TestCase):
    def test_registry_crosses_requested_public_domains(self):
        assert len(SOURCES)>=12
        for category in ("universities","defense","foreign_affairs","business",
                         "environment","news","journals","software","discoveries",
                         "art","music","design","health","funding",
                         "artificial_intelligence","physics"):
            self.assertIn(category,CATEGORIES)
        report=source_catalog()
        self.assertFalse(report["AGI_achieved"])
        self.assertFalse(report["private_military_or_university_systems_accessible"])
        self.assertTrue(report["credential_or_permission_gated"])
        self.assertIn("defense_internal_systems",REVIEW_GATED)

    def test_nature_rdf_rss_namespaced_item(self):
        records=parse_public("nature_journal_news",RDF_RSS)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]["title"],"Measured advances in scientific discovery")
        self.assertEqual(records[0]["published"],"2026-11-06")
        self.assertEqual(records[0]["category"],"journals")
        self.assertFalse(records[0]["independent_fact_check_complete"])

    def test_fixed_hosts_and_bounded_topic(self):
        for key in SOURCES:
            url=request_url(key,"scientific design")
            self.assertEqual(urlsplit(url).netloc,urlsplit(SOURCES[key]["url"]).netloc)
        with self.assertRaises(ValueError):
            request_url("random_remote_provider","research")
        for bad in ("", "a", "research; rm -rf /", "secret=abc&key=123"):
            with self.assertRaises(ValueError):
                scan_horizon(bad)
        with self.assertRaises(ValueError):
            scan_horizon("research",category="not-a-category")

    def test_all_formats_and_provenance(self):
        self.assertEqual(len(parse_public("mit_labs",RSS)),1)
        self.assertEqual(len(parse_public("harvard_research",ATOM)),1)
        key_pairs={
          "crossref_journals":"crossref",
          "gdelt_headlines":"gdelt",
          "world_bank":"world_bank",
          "usgs_earthquakes":"usgs",
          "nasa_natural_events":"eonet",
          "github_public_code":"github",
        }
        for key,kind in key_pairs.items():
            with self.subTest(key=key):
                result=parse_public(key,FIXTURES[kind])
                self.assertEqual(len(result),1)
                self.assertTrue(result[0]["url"].startswith("https://"))
                self.assertTrue(result[0]["untrusted_external_content"])
                self.assertFalse(result[0]["independent_fact_check_complete"])

    def test_dtd_refused(self):
        with self.assertRaises(ValueError):
            parse_public("mit_labs",b'<!DOCTYPE rss><rss/>')

    def test_live_api_scan_mock_handles_outages_without_fabrication(self):
        def opener(req,timeout):
            url=req.full_url
            if urlsplit(url).netloc=="www.defense.gov":
                raise ConnectionError("blocked or unavailable")
            for key,source in SOURCES.items():
                if urlsplit(url).path==urlsplit(source["url"]).path and (
                    urlsplit(url).netloc==urlsplit(source["url"]).netloc):
                    kind=source["type"]
                    return Stream(RSS if kind=="feed" else FIXTURES[kind])
            raise AssertionError(url)
        report=scan_horizon("research and energy",online=True,opener=opener)
        self.assertEqual(report["providers_attempted"],len(SOURCES))
        self.assertEqual(len(report["providers"]),len(SOURCES))
        self.assertEqual(next(x for x in report["providers"] if x["source"]=="dod_public_news")["status"],
                         "unavailable")
        self.assertGreater(report["providers_reporting_data"],3)
        self.assertFalse(report["independent_breakthrough_verified"])
        self.assertFalse(report["AGI_achieved"])
        offline=scan_horizon("research and energy",online=False,
                            opener=lambda *a,**kw:1/0)
        self.assertEqual(len(offline["records"]),0)

if __name__=="__main__":
    unittest.main()
