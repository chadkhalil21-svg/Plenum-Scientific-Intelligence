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
CAS_HTML=b"""<html><section>
<a href="/newsroom/research-news/202611/t20261106_1213515.shtml">
Nov 06, 2026 Chinese Academy of Sciences announces materials research</a>
<a href="https://outside.example/steal">Fake outside</a>
</section></html>"""
CHINA_OPENALEX=json.dumps({"results":[{"id":"https://openalex.org/W123",
 "title":"Chinese university reports photonic research",
 "doi":"https://doi.org/10.1234/example",
 "publication_date":"2026-11-06",
 "authorships":[{"institutions":[{"country_code":"CN"}]}]},
 {"id":"https://openalex.org/W999",
  "title":"Non-Chinese institution is not misattributed",
  "publication_date":"2026-11-05",
  "authorships":[{"institutions":[{"country_code":"US"}]}]}]}).encode()
FIXTURES={
    "china_cas_html":CAS_HTML,
    "china_openalex":CHINA_OPENALEX,
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

    def test_sciencedaily_is_a_secondary_all_fields_headline_feed(self):
        source=SOURCES["sciencedaily_latest"]
        self.assertEqual(source["url"],"https://www.sciencedaily.com/rss/all.xml")
        self.assertEqual(source["category"],"discoveries")
        rss=(b'<?xml version="1.0"?><rss version="2.0"><channel>'
             b'<item><title>A quantum breakthrough makes light behave like both a solid and a liquid</title>'
             b'<link>https://www.sciencedaily.com/releases/2026/11/261105224536.htm</link>'
             b'<pubDate>Mon, 09 Nov 2026 06:19:39 EST</pubDate></item>'
             b'</channel></rss>')
        rows=parse_public("sciencedaily_latest",rss)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["publisher"],"ScienceDaily science news (secondary reporting)")
        self.assertEqual(rows[0]["url"],"https://www.sciencedaily.com/releases/2026/11/261105224536.htm")
        self.assertFalse(rows[0]["primary_source_verified"])
        self.assertFalse(rows[0]["independent_fact_check_complete"])
        with self.assertRaises(ValueError):
            parse_public("sciencedaily_latest",b'<!DOCTYPE fake><rss/>')

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
          "china_cas_research":"china_cas_html",
          "china_openalex_works":"china_openalex",
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


    def test_official_grant_search_subject_filters_before_truncation_and_never_records_token(self):
        query="Survey public agricultural funding sources"
        response={"errorcode":0,"token":"not-persisted",
                  "data":{"oppHits":[
                      {"id":str(i),"title":"Physics opportunity","agencyName":"NSF","oppStatus":"posted"} for i in range(1,8)
                  ]+[
                      {"id":"99","title":"Agricultural research program","agencyName":"USDA","oppStatus":"posted","closeDate":"01/30/2027"},
                      {"id":"100","title":"Agriculture closed grant","agencyName":"USDA","oppStatus":"closed"},
                      {"id":"../101","title":"Agriculture fake grant","agencyName":"USDA","oppStatus":"posted"}]}}
        requests=[]
        def opener(req,timeout):
            requests.append(req)
            if req.full_url=="https://api.grants.gov/v1/api/search2":
                self.assertEqual(req.get_method(),"POST")
                self.assertEqual(json.loads(req.data),{"rows":25,"keyword":"agriculture","oppStatuses":"posted|forecasted"})
                self.assertIsNone(req.get_header("Authorization"))
                return Stream(json.dumps(response).encode())
            return Stream(RSS)
        report=scan_horizon(query,category="funding",online=True,opener=opener)
        self.assertEqual(len(report["records"]),1)
        self.assertEqual(report["records"][0]["url"],"https://www.grants.gov/search-results-detail/99")
        self.assertEqual(report["records"][0]["title"],"Agricultural research program")
        self.assertNotIn("not-persisted",json.dumps(report))
        self.assertFalse(report["records"][0]["primary_source_verified"])
        self.assertFalse(report["records"][0]["independent_fact_check_complete"])
        self.assertEqual(len(requests),2)


    def test_paper_survey_uses_topic_not_instruction_and_filters_before_limit(self):
        from urllib.parse import parse_qs
        calls=[]
        def opener(req,timeout):
            calls.append(req.full_url)
            query=parse_qs(urlsplit(req.full_url).query)
            self.assertEqual(query["query.title"],["photonic computing"])
            self.assertEqual(query["rows"],["20"])
            rows=[{"title":["Unrelated survey of papers"],"DOI":"10.1000/wrong"+str(i)} for i in range(5)]
            rows += [{"title":["Photonic computation architectures"],"DOI":"10.1000/right"},
                     {"title":["Photonic computing"],"DOI":"invalid"}]
            return Stream(json.dumps({"message":{"items":rows}}).encode())
        report=scan_horizon("Survey public photonic computing papers",category="journals",online=True,opener=opener)
        self.assertEqual(len(calls),1)
        self.assertEqual([r["url"] for r in report["records"]],["https://doi.org/10.1000/right"])
        self.assertFalse(report["records"][0]["independent_fact_check_complete"])

    def test_paper_search_changes_strategy_once_when_first_results_are_irrelevant(self):
        from urllib.parse import parse_qs
        calls=[]
        def opener(req,timeout):
            q=parse_qs(urlsplit(req.full_url).query)
            calls.append(q)
            rows=[{"title":["Unrelated survey"],"DOI":"10.1000/irrelevant"}]
            if "query.bibliographic" in q:
                rows.append({"title":["Photonic computation architecture"],"DOI":"10.1000/recovered"})
            return Stream(json.dumps({"message":{"items":rows}}).encode())
        report=scan_horizon("Survey public photonic computing papers",category="journals",online=True,opener=opener)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0]["query.title"],["photonic computing"])
        self.assertEqual(calls[1]["query.bibliographic"],["photonic computing"])
        self.assertEqual([r["url"] for r in report["records"]],["https://doi.org/10.1000/recovered"])
        self.assertEqual(report["providers"][0]["first_attempt"]["records"],[])
        self.assertEqual(report["providers"][0]["query_strategy"],"bibliographic_recovery")


if __name__=="__main__":
    unittest.main()
