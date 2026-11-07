"""China public research sources use only permitted institutional and scholarly metadata."""
import json, unittest
from urllib.parse import parse_qs,urlsplit
from plenum_ai.world_horizon import request_url,parse_public
from plenum_ai.china_sources import cas_research_articles,china_affiliated_works

CAS=b'''<a href="../research-news/202611/t20261106_1213515.shtml">Nov 06, 2026
 New study in moire superlattices</a><a href="https://evil.example/x">Do not collect me</a>'''
OPEN=json.dumps({"results":[
 {"id":"https://openalex.org/W42","title":"China-affiliated photonics result",
  "publication_date":"2026-11-06","doi":"https://doi.org/10.1000/china",
  "authorships":[{"institutions":[{"country_code":"CN"}]}]},
 {"id":"https://openalex.org/W33","title":"US-only result",
  "publication_date":"2026-11-06","authorships":[{"institutions":[{"country_code":"US"}]}]}
]}).encode()
class ChinaSourcesTests(unittest.TestCase):
    def test_public_cas_link_and_no_offsite(self):
        rows=parse_public("china_cas_research",CAS)
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]["url"].startswith("https://english.cas.cn/"))
        self.assertFalse(rows[0]["independent_fact_check_complete"])
    def test_cn_affiliation_filter_is_not_all_china(self):
        rows=parse_public("china_openalex_works",OPEN)
        self.assertEqual(len(rows),1)
        self.assertIn("China-affiliated",rows[0]["metadata_note"])
        self.assertEqual(rows[0]["url"],"https://doi.org/10.1000/china")
        url=request_url("china_openalex_works","global science")
        query=parse_qs(urlsplit(url).query)
        self.assertIn("institutions.country_code:CN",query["filter"][0])
        self.assertEqual(query["per_page"],["4"])
    def test_unknown_and_wrong_formats_fail(self):
        with self.assertRaises(ValueError):cas_research_articles(b'<a href="https://fake/x">fake</a>')
        with self.assertRaises(ValueError):china_affiliated_works(b'{"message":"missing results"}')
        with self.assertRaises(ValueError):parse_public("china_cas_research",b'X' * 1250001)
if __name__=="__main__":unittest.main()
