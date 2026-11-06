"""Offline verification of journal, preprint, institutional and YouTube sources."""
from datetime import datetime, timezone
from urllib.parse import urlsplit
import io
import json
import unittest
from plenum_ai.discovery_watch import (
    JOURNALS,LAB_FEEDS,crossref_url,parse_crossref,
    preprint_url,parse_preprints,parse_newsfeed,youtube_url,
    parse_youtube,research_pulse
)

WHEN=datetime(2026,11,6,12,0,tzinfo=timezone.utc)
JOURNAL=json.dumps({"message":{"items":[{
    "type":"journal-article","DOI":"10.5555/physics-demo",
    "title":["Verified title in scholarly metadata"],
    "published":{"date-parts":[[2026,11,5]]}
}]}}).encode()
PREPRINT=json.dumps({"collection":[{
    "doi":"10.1101/2026.11.05.123456",
    "title":"Fresh scientific hypothesis awaiting peer review",
    "date":"2026-11-05","category":"physics"
}]}).encode()
MIT=b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>MIT materials breakthrough claim</title><link>https://news.mit.edu/2026/new-lab-activity</link><pubDate>Thu, 05 Nov 2026 12:00:00 GMT</pubDate></item>
</channel></rss>"""
NASA=b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>NASA research update</title><link>https://www.nasa.gov/news-release/test/</link></item>
</channel></rss>"""
YOUTUBE=b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"
xmlns:yt="http://www.youtube.com/xml/schemas/2015">
<entry><yt:videoId>AbCdEf12345</yt:videoId>
<title>NASA's new telescope</title><published>2026-11-05T13:00:00+00:00</published></entry>
</feed>"""


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()


class ResearchPulseTests(unittest.TestCase):
    def test_crossref_known_journal_and_no_unverified_peer_review(self):
        self.assertGreaterEqual(len(JOURNALS),18)
        self.assertIn("/journals/0028-0836/works?",crossref_url("0028-0836",WHEN))
        with self.assertRaises(ValueError):
            crossref_url("1234-5678",WHEN)
        result=parse_crossref(JOURNAL,"Nature",WHEN)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["published"],"2026-11-05")
        self.assertFalse(result[0]["independently_peer_reviewed"])
        self.assertFalse(result[0]["full_text_available"])

    def test_preprints_flag_not_peer_reviewed(self):
        self.assertIn("/biorxiv/7d/0/json",preprint_url("biorxiv"))
        with self.assertRaises(ValueError):
            preprint_url("no-server")
        rows=parse_preprints(PREPRINT,"biorxiv")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["tier"],"preprint_not_peer_reviewed")
        self.assertFalse(rows[0]["claims_verified"])

    def test_institutional_feeds_and_youtube_only_metadata(self):
        self.assertEqual(len(parse_newsfeed(MIT,"MIT News")),1)
        self.assertEqual(len(parse_newsfeed(NASA,"NASA Updates")),1)
        self.assertIn("channel_id=UCLA_DiR1FfKNvjuUpBHmylQ",youtube_url())
        with self.assertRaises(ValueError):
            youtube_url("unreviewed-person")
        rows=parse_youtube(YOUTUBE)
        self.assertEqual(rows[0]["url"],"https://www.youtube.com/watch?v=AbCdEf12345")
        self.assertFalse(rows[0]["video_downloaded"])
        self.assertFalse(rows[0]["transcript_available_or_licensed"])
        with self.assertRaises(ValueError):
            parse_youtube(b"<!DOCTYPE lol><feed/>")

    def test_complete_six_provider_offline_fixture(self):
        urls=[]
        def opener(request,timeout):
            url=request.full_url
            urls.append(url)
            host=urlsplit(url).hostname
            if host=="api.crossref.org": return Response(JOURNAL)
            if host=="api.biorxiv.org": return Response(PREPRINT)
            if host=="news.mit.edu": return Response(MIT)
            if host=="www.nasa.gov": return Response(NASA)
            if host=="www.youtube.com": return Response(YOUTUBE)
            raise AssertionError("Unexpected network host")
        report=research_pulse("photonic batteries",cutoff=WHEN,opener=opener,
                              selected_journals=["Nature"])
        self.assertEqual(len(report["providers"]),6)
        self.assertEqual(report["distinct_records"],5)
        self.assertTrue(all(x["status"]=="retrieved_metadata" for x in report["providers"]))
        self.assertFalse(report["breakthroughs_independently_confirmed"])
        self.assertFalse(report["all_science_journals_covered"])
        self.assertFalse(report["video_transcripts_downloaded"])

    def test_failed_provider_does_not_block_other_research(self):
        def opener(request,timeout):
            host=urlsplit(request.full_url).hostname
            if host=="www.youtube.com": raise ConnectionError("YouTube unavailable")
            if host=="api.crossref.org": return Response(JOURNAL)
            if host=="api.biorxiv.org": return Response(PREPRINT)
            if host=="news.mit.edu": return Response(MIT)
            return Response(NASA)
        report=research_pulse("astronomy",cutoff=WHEN,opener=opener,
                              selected_journals=["Nature"])
        self.assertIn("youtube-nasa",report["sources_unavailable"])
        self.assertGreater(len(report["records"]),0)

if __name__=="__main__":
    unittest.main()
