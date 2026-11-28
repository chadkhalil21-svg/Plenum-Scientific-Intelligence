"""Independent review only: no network access or candidate implementation."""
import unittest
from plenum_ai.world_horizon import parse_public

KEY = "mit_music_research"
FEED = '<rss version="2.0"><channel><item><title>Public research news</title><link>https://news.mit.edu/example</link></item></channel></rss>'
ATOM = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Public research news</title><link href="https://news.mit.edu/example"/></entry></feed>'

class PublicXMLBoundary(unittest.TestCase):
    def test_valid_feed_across_encodings(self):
        for xml in (FEED, ATOM):
            for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
                with self.subTest(encoding=encoding, root=xml[:12]):
                    records = parse_public(KEY, xml.encode(encoding))
                    self.assertEqual(len(records), 1)
                    self.assertEqual(records[0]["title"], "Public research news")
                    self.assertEqual(records[0]["url"], "https://news.mit.edu/example")

    def test_dtd_rejected_across_encodings(self):
        for xml, root in ((FEED, "rss"), (ATOM, "feed")):
            for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
                with self.subTest(encoding=encoding, root=root):
                    # Harmless empty declaration; no expansion or external resource.
                    with self.assertRaises(ValueError):
                        parse_public(KEY, ("<!DOCTYPE " + root + " []>" + xml).encode(encoding))

    def test_ordinary_malformed_xml_stays_rejected(self):
        with self.assertRaises(Exception):
            parse_public(KEY, b"<rss><channel>")

if __name__ == "__main__":
    unittest.main()
