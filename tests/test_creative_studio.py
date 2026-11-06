"""Verify cross-domain creative discovery and original derivative-free outputs."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from plenum_ai.creative_sources import (
    openverse_url,parse_openverse,museum_search_url,parse_museum_search,
    museum_object_url,parse_museum_object,musicbrainz_url,
    parse_musicbrainz,creative_discovery
)
from plenum_ai.creative_studio import (
    svg_study,musicxml_study,idea_studies,write_studies
)

MEDIA=json.dumps({"results":[{
    "title":"Geometric public-domain reference","foreign_landing_url":"https://example.org/art/1",
    "creator":"Research Museum","license":"cc0","license_version":"1.0",
    "license_url":"https://creativecommons.org/publicdomain/zero/1.0",
    "attribution":"Research Museum"
}]}).encode()
MET_LIST=b'{"total": 1, "objectIDs": [12]}'
MET_OBJECT=json.dumps({
    "objectID":12,"title":"Ancient design object",
    "objectURL":"https://www.metmuseum.org/art/collection/search/12",
    "artistDisplayName":"Historic creator","isPublicDomain":True
}).encode()
MUSIC=json.dumps({"works":[{
    "title":"A descriptive work title",
    "id":"c789a96f-13d2-4a94-a9a1-1df79aa9ed23","type":"Song"
}]}).encode()

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args):self.close()


class CreativeConnectionsTests(unittest.TestCase):
    def test_sources_read_only_and_licensed(self):
        self.assertIn("/v1/images/",openverse_url("geometry","images"))
        self.assertIn("/v1/audio/",openverse_url("music","audio"))
        self.assertIn("/v1.1/search",museum_search_url("architectural"))
        self.assertIn("/ws/2/work/",musicbrainz_url("symphony"))
        self.assertEqual(parse_museum_search(MET_LIST),[12])
        self.assertTrue(parse_museum_object(MET_OBJECT)["public_domain_flag"])
        self.assertIsNone(parse_museum_object(json.dumps({
            "objectID":13,"isPublicDomain":False
        }).encode() if False else {"objectID":13,"isPublicDomain":False}))
        self.assertFalse(parse_openverse(MEDIA,"images")[0]["downloaded"])
        self.assertFalse(parse_musicbrainz(MUSIC)[0]["permission_to_reproduce_music"])

    def test_four_creative_source_lookups(self):
        def opener(req,timeout):
            url=req.full_url
            host=urlsplit(url).hostname
            if host=="api.openverse.org": return Response(MEDIA)
            if host=="collectionapi.metmuseum.org":
                return Response(MET_LIST if "/search?" in url else MET_OBJECT)
            if host=="musicbrainz.org": return Response(MUSIC)
            raise AssertionError(host)
        report=creative_discovery("geometric music",opener=opener)
        self.assertEqual(report["source_count"],4)
        self.assertEqual(len(report["records"]),4)
        self.assertFalse(report["assets_downloaded"])
        self.assertFalse(report["generative_ai_model_connected"])

    def test_offline_original_svg_notation_and_ideas(self):
        svg=svg_study("living architecture",4321)
        score=musicxml_study("living architecture",4321)
        self.assertEqual(svg,svg_study("living architecture",4321))
        self.assertEqual(score,musicxml_study("living architecture",4321))
        self.assertEqual(ET.fromstring(svg).tag,"{http://www.w3.org/2000/svg}svg")
        self.assertEqual(ET.fromstring(score).tag,"score-partwise")
        self.assertEqual(len(ET.fromstring(score).findall(".//note")),32)
        result=idea_studies("living architecture",4321)
        self.assertEqual(len(result["concepts"]),5)
        self.assertFalse(result["AI_creative_reasoning_used"])
        with tempfile.TemporaryDirectory() as root:
            out=write_studies("living architecture",4321,root)
            self.assertTrue(all(Path(p).is_file() for p in out["outputs"].values()))
            with self.assertRaises(FileExistsError):
                write_studies("living architecture",4321,root)

    def test_bounded_untrusted_inputs(self):
        with self.assertRaises(ValueError):
            svg_study("<script>alert(1)</script>"*50)
        with self.assertRaises(ValueError):
            musicxml_study("short",1000001)
        with self.assertRaises(ValueError):
            openverse_url("art","unknown")

if __name__=="__main__":
    unittest.main()
